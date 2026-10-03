"""Top-level widget of the stage visualizer.

Combines the 3D viewport, the editor panel and the DMX poller behind a
single QSplitter and relays signals between them.

"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, override

from PySide6 import QtCore, QtWidgets

from model.broadcaster import Broadcaster
from model.visualizer.dmx.dmx_parser import (
    ColorRole,
    DmxParser,
    MovementRole,
    auto_detect_mapping,
    get_movement_range,
)
from model.visualizer.stage.fixture_group import FixtureGroup
from model.visualizer.stage.so_moving_head import MovingHead
from model.visualizer.stage.so_par_can import ParCan
from model.visualizer.stage.so_pixel_fixture import PixelFixture
from model.visualizer.stage.stage_config import (
    STAGE_DIR,
    StageConfig,
    backup_stage_file,
    create_object_from_key,
    get_default_stage_path,
)
from view.visualizer.stage_editor_widget import StageEditorWidget
from view.visualizer.stage_gl_widget import Stage3DWidget

if TYPE_CHECKING:
    from PySide6 import QtGui
    from PySide6.QtWidgets import QWidget

    from model import BoardConfiguration
    from model.ofl.fixture import UsedFixture
    from model.visualizer.stage.stage_object import StageObject

logger = getLogger(__name__)

# Single-word roles handled by the fast path in :func:`_classify_pixel_channel`.
_PIXEL_COLOUR_ROLES: dict[str, str] = {
    "red": "red",
    "green": "green",
    "blue": "blue",
    "amber": "amber",
    "uv": "uv",
    "ultraviolet": "uv",
    "white": "white",
}
# Two-word colour prefixes checked before falling back to the single-word map.
# Ordered so that the more specific prefixes (warm/cold/cool white) win over "white".
_PIXEL_COLOUR_PREFIXES: tuple[tuple[str, str], ...] = (
    ("warm white", "warm_white"),
    ("cold white", "cold_white"),
    ("cool white", "cold_white"),
    ("warmwhite", "warm_white"),
    ("coldwhite", "cold_white"),
    ("coolwhite", "cold_white"),
)
_DIMMER_ROLE_WORDS = ("dimmer", "intensity", "master dimmer", "master intensity")

# Short keys used inside each pixel entry of ``device_config["pixels"]["channels"]``.
_ROLE_TO_ENTRY_KEY: dict[str, str] = {
    "red": "r",
    "green": "g",
    "blue": "b",
    "white": "w",
    "cold_white": "cw",
    "warm_white": "ww",
    "amber": "a",
    "uv": "uv",
}


def _classify_pixel_channel(name: str) -> tuple[str, str | None]:
    """Parse a fixture channel name into ``(role, pixel_key)``.

    Roles are one of ``red|green|blue|white|cold_white|warm_white|amber|uv|dimmer|unknown``.
    ``pixel_key`` is the identifier string that follows the role word (e.g. ``"(0, 0, 0)"``
    from ``eachPixelXYZ`` or a custom ``pixelKey`` from ``eachPixelABC``); it is
    ``None`` for global fixture-wide channels like a leading master dimmer.
    """
    text = (name or "").strip()
    if not text:
        return "unknown", None
    lower = text.lower()

    # Two-word colour prefixes (warm/cold/cool white) must be tried before the
    # single-word "white" fallback, otherwise "Warm White" would classify as "white".
    for prefix, role in _PIXEL_COLOUR_PREFIXES:
        if lower.startswith(prefix):
            tail = text[len(prefix):].strip()
            return role, tail or None

    parts = text.split(maxsplit=1)
    head = parts[0].lower()
    tail = parts[1].strip() if len(parts) > 1 else ""

    if head in _PIXEL_COLOUR_ROLES:
        return _PIXEL_COLOUR_ROLES[head], tail or None

    if any(lower == word or lower.startswith(word + " ") for word in _DIMMER_ROLE_WORDS):
        return "dimmer", None

    return "unknown", None


def _build_color_section(device: UsedFixture) -> dict[str, Any] | None:
    """Build the ``color`` section of ``device_config`` for a beam fixture.

    Combines auto-detected per-colour-role channel offsets with the first
    colour-carrying wheel extracted via :func:`_extract_wheel_configs`. Returns
    ``None`` if the fixture exposes no colour source at all so the caller can
    skip adding an empty section to ``device_config``.
    """
    ch_names = [ch.name for ch in device.fixture_channels]
    col_mapping = auto_detect_mapping(ch_names, ColorRole)
    wheel_configs = _extract_wheel_configs(device)

    has_direct = any(col_mapping.get(role, -1) >= 0 for role in ("red", "green", "blue", "white", "amber", "uv"))
    if not has_direct and not wheel_configs:
        return None

    cfg: dict[str, Any] = {
        "universe": device.universe_id,
        "start_channel": device.start_index,
        "channel_count": device.channel_length,
        "mapping": col_mapping,
    }
    if wheel_configs:
        # Fixtures rarely carry more than one colour-contributing wheel; take the
        # first and fold its slot colours into the beam colour alongside any RGB.
        cfg["wheel"] = wheel_configs[0]
    return cfg


def _extract_wheel_configs(device: UsedFixture) -> list[dict[str, Any]]:
    """Build ``[{channel, slots: [{dmx_min, dmx_max, color}]}, ...]`` for wheel channels.

    Uses each channel's template ``WheelSlot`` capabilities together with the
    fixture-level ``wheels`` dict; the slot's :meth:`WheelSlot.resulting_color`
    (which understands ``colorTemperature``, colour name lookup and open/closed
    slots) is converted to 0-255 RGB. Slots without a resolvable colour or with
    a non-integer ``slotNumber`` (interpolation between slots) are skipped.
    """
    # Local imports keep the module import surface small and avoid pulling the OFL
    # code into the visualizer package for the RGB(W) fast path.
    from model.ofl.ofl_fixture import CapabilityType

    fixture = getattr(device, "_fixture", None)
    if fixture is None:
        return []

    wheel_defs = getattr(fixture, "wheels", None) or {}
    if not wheel_defs:
        return []

    wheels_out: list[dict[str, Any]] = []
    for offset, ch in enumerate(device.fixture_channels):
        template = ch.channel_template
        if template is None:
            continue
        wheel = wheel_defs.get(ch.name)
        if wheel is None or not wheel.slots:
            continue

        slots: list[dict[str, Any]] = []
        for capability in template.get_capabilities():
            if capability.type != CapabilityType.WHEEL_SLOT:
                continue
            slot_number = capability.capabilityProperties.get("slotNumber")
            if not isinstance(slot_number, int) or isinstance(slot_number, bool):
                # slotNumber is a float for transitions between slots; skip those
                # so we only mix in colours the wheel actually locks onto.
                continue
            index = (slot_number - 1) % len(wheel.slots)
            wheel_slot = wheel.slots[index]
            try:
                r, g, b = wheel_slot.resulting_color.to_rgb()
            except Exception as e:
                logger.debug("Could not resolve wheel slot colour on %s: %s", ch.name, e)
                continue
            dmx_range = capability.dmxRange
            dmx_min = int(dmx_range[0]) if len(dmx_range) > 0 else 0
            dmx_max = int(dmx_range[1]) if len(dmx_range) > 1 else dmx_min
            slots.append(
                {
                    "dmx_min": dmx_min,
                    "dmx_max": dmx_max,
                    "color": [int(r), int(g), int(b)],
                }
            )

        if slots and any(any(s.get("color", (0, 0, 0))) for s in slots):
            # Skip wheels whose slots are all black (typical for gobo wheels,
            # where resulting_color falls back to black for unnamed shapes).
            wheels_out.append({"channel": device.start_index + offset, "slots": slots})
    return wheels_out


class StageVisualizerWidget(QtWidgets.QSplitter):
    """Horizontal split: 3D viewport on the left, editor panel on the right."""

    def __init__(self, board_configuration: BoardConfiguration, parent: QWidget | None = None) -> None:
        """Initialize using provided show file and parent object."""
        super().__init__(parent)
        self._broadcaster = Broadcaster()
        self._board_configuration = board_configuration

        self.setOrientation(QtCore.Qt.Orientation.Horizontal)

        stage_path = board_configuration.ui_hints.get("associated_stage_file", get_default_stage_path())
        logger.info("Loading stage from %s", stage_path)
        self._stage_config = StageConfig(stage_path, show_file_path=board_configuration.file_path)

        self._gl_widget = Stage3DWidget(self._stage_config, parent=self)
        self._editor_widget = StageEditorWidget(
            self._stage_config,
            used_fixtures=self._get_fixtures(),
            parent=self,
        )
        self.addWidget(self._gl_widget)
        self.addWidget(self._editor_widget)

        # 3D viewport takes most of the width.
        self.setStretchFactor(0, 1)
        self.setStretchFactor(1, 0)
        self.setSizes([2200, 360])

        # Editor -> mediator
        self._editor_widget.add_object_requested.connect(self._on_add_object)
        self._editor_widget.remove_object_requested.connect(self._on_remove_object)
        self._editor_widget.object_changed.connect(self._on_object_changed)
        self._editor_widget.selection_changed.connect(self._on_selection_changed)
        self._editor_widget.group_requested.connect(self._on_group_requested)
        self._editor_widget.remove_group_requested.connect(self._on_remove_group)
        self._editor_widget.dmx_toggled.connect(self._on_dmx_toggled)

        # 3D viewport -> mediator
        self._gl_widget.fixture_clicked.connect(self._on_fixture_clicked)
        self._gl_widget.deselect_all_requested.connect(self._on_deselect_all)

        self._dmx_vis = DmxParser(
            self._stage_config,
            board_configuration=board_configuration,
            parent=self,
        )
        self._dmx_vis.fixtures_updated.connect(self._on_dmx_updated)
        self._update_dmx_polling()

        # Refresh fixture list when the show file changes.
        self._broadcaster.show_file_loaded.connect(self._refresh_fixtures)
        self._broadcaster.show_file_loaded.connect(
            lambda: self._reload_stage(self._board_configuration.ui_hints.get("associated_stage_file", ""))
        )
        self._broadcaster.show_file_path_changed.connect(lambda _: self._refresh_fixtures())
        self._broadcaster.connection_state_updated.connect(self._on_connection_state_updated)
        self._broadcaster.add_fixture.connect(lambda _fix: self._refresh_fixtures())

        self._broadcaster.application_closing.connect(self._on_app_closing)

        self._save_timer = QtCore.QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self._save_stage)
        self._save_failed = False

        # When the show file was loaded before the visualizer was constructed,
        # the ``show_file_loaded`` signal never fires here. Run the backfill once
        # against whatever fixtures the board already knows about.
        if self._backfill_color_sections():
            self._schedule_save()

    @override
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Start DMX polling once the visualizer becomes visible."""
        super().showEvent(event)
        self._update_dmx_polling()

    @override
    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        """Stop DMX polling while the visualizer tab is hidden."""
        super().hideEvent(event)
        self._update_dmx_polling()

    def _on_app_closing(self) -> None:
        """Flush pending debounced saves when the application shuts down."""
        self._save_stage()

    def load_stage_file(self) -> None:
        """Opens a file dialog to query a stage file and loads it."""
        # FIXME this is a blocking UI call.
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Stagefile", STAGE_DIR, "Stage Files (*.yaml *.yml);;All Files (*)"
        )
        if not path:
            return

        backup = backup_stage_file(self._stage_config.file_path)
        if backup:
            logger.info("Current stage backed up to %s", backup)

        self._reload_stage(path)

    def save_stage_file(self) -> None:
        """Displays a save file dialog and saves the current stage setup into a stage file."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Stagefile", STAGE_DIR, "Stage Files (*.yaml *.yml);;All Files (*)"
        )
        if not path:
            return
        if not self._stage_config.save_to(path):
            QtWidgets.QMessageBox.warning(self, "Stage", f"The stage file could not be saved:\n{path}")
            return
        logger.info("Stage saved to %s", path)

    def _reload_stage(self, new_path: str) -> None:
        logger.info("Switching to new stage: %s", new_path)

        self._save_stage()
        new_config = StageConfig(new_path, show_file_path=self._board_configuration.file_path)

        for obj in new_config.objects:
            if hasattr(obj, "device_config") and obj.device_config:
                dc = obj.device_config
                if "movement" in dc and "pan_tilt_range" not in dc["movement"]:
                    self._populate_pan_tilt_range_for_object(obj, dc["movement"])

        self._stage_config = new_config
        self._dmx_vis.set_stage_config(new_config)
        self._gl_widget.set_stage_config(new_config)
        self._editor_widget.set_stage_config(new_config)

        # Backfill the ``color`` section on beam fixtures (MovingHead / ParCan)
        # that were saved before the auto-config knew how to detect RGB(W/A/UV)
        # and colour wheels. Also persist, so the stage file converges once the
        # user re-opens it with the show file loaded.
        if self._backfill_color_sections():
            self._schedule_save()

        logger.info("Stage loaded: %d objects", len(new_config.objects))

    def _backfill_color_sections(self) -> bool:
        """Add missing ``color`` sections to loaded beam fixtures.

        Walks the current :class:`StageConfig` and, for every :class:`MovingHead`
        or :class:`ParCan` whose ``device_config`` has a ``movement`` entry but
        no ``color`` entry, looks up the fixture at that DMX address in the
        board configuration and runs :func:`_build_color_section` to synthesise
        one (RGB/W/A/UV channels and the first colour wheel, if any).

        Returns:
            ``True`` if at least one object was upgraded, so the caller can
            schedule a save.

        """
        if not self._stage_config.objects:
            return False
        upgraded = False
        for obj in self._stage_config.objects:
            if not isinstance(obj, (MovingHead, ParCan)):
                continue
            dc = obj.device_config
            if not dc or "color" in dc:
                continue
            mv = dc.get("movement") or {}
            universe = mv.get("universe")
            start = mv.get("start_channel")
            if universe is None or start is None:
                continue
            fixture = self._find_fixture_by_address(int(universe), int(start))
            if fixture is None:
                continue
            try:
                color_cfg = _build_color_section(fixture)
            except Exception as e:
                logger.debug("Could not backfill colour section for %s: %s", obj.id, e)
                continue
            if color_cfg is None:
                continue
            dc["color"] = color_cfg
            upgraded = True
            logger.info(
                "Backfilled DMX colour section for %s (%s) from %s",
                obj.id,
                obj.get_type(),
                fixture.name,
            )
        return upgraded

    def _find_fixture_by_address(self, universe: int, start_channel: int) -> UsedFixture | None:
        """Return the patched fixture at the given DMX base address, or ``None``."""
        try:
            for fixture in self._board_configuration.fixtures:
                if fixture.universe_id == universe and fixture.start_index == start_channel:
                    return fixture
        except Exception:
            return None
        return None

    def _populate_pan_tilt_range_for_object(self, obj: StageObject, movement_cfg: dict[str, Any]) -> None:
        if "universe" not in movement_cfg or "start_channel" not in movement_cfg:
            return

        try:
            for fixture in self._board_configuration.fixtures:
                if fixture.universe_id == movement_cfg.get("universe") and fixture.start_index == movement_cfg.get(
                    "start_channel"
                ):
                    movement_cfg["pan_tilt_range"] = get_movement_range(fixture)
                    break
        except Exception as e:
            logger.debug("Could not populate pan_tilt_range: %s", e)

    def _get_fixtures(self) -> list[UsedFixture]:
        try:
            return list(self._board_configuration.fixtures)
        except Exception:
            return []

    def _refresh_fixtures(self) -> None:
        self._editor_widget.set_used_fixtures(self._get_fixtures())
        # Fixtures may have appeared or changed address; try again to backfill
        # colour sections on any beam fixtures that are still missing one.
        if self._backfill_color_sections():
            self._schedule_save()
            self._gl_widget.update()

    def _on_connection_state_updated(self, connected: bool) -> None:
        """Refresh the fixture list shortly after a connection to Fish was established.

        The delay gives Fish time to publish its show file and fixture list
        before the visualizer reads them.
        """
        if connected:
            QtCore.QTimer.singleShot(500, self._refresh_fixtures)

    def _on_add_object(self, fixture_key: str, name: str, device: UsedFixture) -> None:
        new_id = self._stage_config.get_new_id(fixture_key)
        try:
            new_obj = create_object_from_key(fixture_key, new_id, name)
        except Exception as e:
            logger.error("Failed to create object: %s", e)
            return

        # Auto-link the selected DMX device, if any.
        if device is not None:
            try:
                if isinstance(new_obj, PixelFixture):
                    self._auto_configure_pixel_fixture(new_obj, device)
                elif isinstance(new_obj, ParCan):
                    self._auto_configure_par_can(new_obj, device)
                else:
                    ch_names = [ch.name for ch in device.fixture_channels]
                    mapping = auto_detect_mapping(ch_names, MovementRole)
                    dc: dict[str, Any] = {
                        "movement": {
                            "universe": device.universe_id,
                            "start_channel": device.start_index,
                            "channel_count": device.channel_length,
                            "mapping": mapping,
                            "pan_tilt_range": get_movement_range(device),
                        }
                    }
                    # Pick up RGB(W/A/UV) channels and any colour wheel so wheel-only
                    # moving heads (no RGB channels) still drive the beam colour.
                    color_cfg = _build_color_section(device)
                    if color_cfg is not None:
                        dc["color"] = color_cfg
                    new_obj.device_config = dc
            except Exception as e:
                logger.warning("Could not auto-link device: %s", e)

        self._stage_config.add_object(new_obj)
        self._editor_widget.add_object_to_list(new_obj)

        self._gl_widget.makeCurrent()
        self._gl_widget.load_object(new_obj)
        self._gl_widget.doneCurrent()
        self._gl_widget.update()
        self._save_stage()

    def _auto_configure_par_can(self, obj: ParCan, device: UsedFixture) -> None:
        """Populate a PAR can's ``device_config`` from a linked OFL fixture.

        Auto-detects both a dimmer channel (stored under the ``movement`` key so it
        travels the same code path as :meth:`DmxParser._apply_movement`) and RGB/W
        colour channels (under the ``color`` key). Both point at the same device
        since a PAR can typically drives all its channels from a single fixture.
        """
        ch_names = [ch.name for ch in device.fixture_channels]
        mv_mapping = auto_detect_mapping(ch_names, MovementRole)

        dc: dict[str, Any] = {}
        if mv_mapping.get(MovementRole.DIMMER.value, -1) >= 0:
            dc["movement"] = {
                "universe": device.universe_id,
                "start_channel": device.start_index,
                "channel_count": device.channel_length,
                "mapping": mv_mapping,
            }
        color_cfg = _build_color_section(device)
        if color_cfg is not None:
            dc["color"] = color_cfg
        obj.device_config = dc or None

    def _auto_configure_pixel_fixture(self, obj: PixelFixture, device: UsedFixture) -> None:
        """Populate matrix layout, dimensions and per-pixel DMX mapping from an OFL fixture.

        Parses channel names to find per-pixel R/G/B/W channels and any global
        dimmer / intensity channel. This is name-based (rather than segment-map based)
        because matrix-generated channels in the OFL importer are currently created
        without a channel template, so their :class:`FixtureChannelType` stays
        ``UNDEFINED`` and the type-based segment maps come back empty.
        """
        # Grid shape: prefer OFL matrix.pixelCount, but the channel-parsing pass below
        # can override it if the actual channel count implies a different layout.
        matrix = getattr(device, "_fixture", None)
        if matrix is not None and hasattr(matrix, "matrix"):
            pc = matrix.matrix.pixelCount
            cols = max(1, int(pc[0]))
            rows = max(1, int(pc[1] or 1))
            # Some bar-style fixtures declare pixels along a single axis.
            if rows == 1 and pc[2] and int(pc[2]) > 1:
                rows = int(pc[2])
            obj.pixel_matrix = (cols, rows)

            dims = matrix.physical.dimensions
            if any(dims):
                w = float(dims[0]) if dims[0] else obj.physical_size[0]
                h = float(dims[1]) if dims[1] else obj.physical_size[1]
                d = float(dims[2]) if dims[2] else obj.physical_size[2]
                obj.physical_size = (w, h, d)

        universe_id = device.universe_id
        start = device.start_index

        # Walk the channel list, classify each channel and group per-pixel channels
        # by the pixel identifier that follows the role word (e.g. "(0, 0, 0)" from
        # ``eachPixelXYZ`` or a custom pixelKey string from ``eachPixelABC``).
        per_pixel: dict[str, dict[str, int]] = {}
        pixel_order: list[str] = []
        global_dimmer_channel = -1

        for offset, ch in enumerate(device.fixture_channels):
            abs_channel = start + offset
            role, key = _classify_pixel_channel(ch.name)
            if role == "dimmer" and key is None:
                if global_dimmer_channel < 0:
                    global_dimmer_channel = abs_channel
                continue
            entry_key = _ROLE_TO_ENTRY_KEY.get(role)
            if entry_key is None:
                continue
            pixel_key = key if key is not None else "single"
            if pixel_key not in per_pixel:
                per_pixel[pixel_key] = {}
                pixel_order.append(pixel_key)
            per_pixel[pixel_key][entry_key] = abs_channel

        # Reconcile matrix layout with the actual per-pixel channel count. If the
        # fixture provided distinct per-pixel channels but the OFL matrix layout
        # doesn't match, collapse to a single row rather than silently dropping pixels.
        derived = len(pixel_order)
        if derived > 0 and derived != obj.pixel_matrix[0] * obj.pixel_matrix[1]:
            obj.pixel_matrix = (derived, 1)

        entries = [per_pixel[k] for k in pixel_order]

        # Colour wheels are fixture-wide; store the first one at the top level so
        # every pixel shares it when the parser computes the pixel colour.
        wheel_configs = _extract_wheel_configs(device)

        pixels_cfg: dict[str, Any] = {
            "universe": universe_id,
            "start_channel": start,
            "channel_count": device.channel_length,
            "channels": entries,
        }
        if global_dimmer_channel >= 0:
            pixels_cfg["dimmer"] = global_dimmer_channel
        if wheel_configs:
            pixels_cfg["wheel"] = wheel_configs[0]

        obj.device_config = {"pixels": pixels_cfg}

    def _on_remove_object(self, object_id: str) -> None:
        obj = self._stage_config.remove_object(object_id)
        if not obj:
            return
        self._editor_widget.remove_object_from_list(object_id)
        self._gl_widget.makeCurrent()
        self._gl_widget.remove_object(obj)
        self._gl_widget.doneCurrent()
        self._gl_widget.update()
        self._save_stage()
        self._editor_widget.refresh_list()

    def _on_object_changed(self, object_id: str) -> None:
        obj = self._stage_config.get_object(object_id)
        if obj is not None and hasattr(obj, "get_procedural_mesh_data"):
            # Matrix or dimensions may have changed; rebuild the mesh so the
            # cuboid + recessed lenses match the new configuration on next draw.
            self._gl_widget.reload_object_models(obj)
        self._gl_widget.update()
        self._schedule_save()

    def _on_selection_changed(self, object_ids: list, is_multi: bool) -> None:
        self._gl_widget.set_selected_objects(object_ids, is_multi)
        self._gl_widget.update()

    def _on_group_requested(self, fixture_ids: list, group_name: str) -> None:
        if len(fixture_ids) < 2:
            return

        # Pull fixtures out of any existing group first.
        for fid in fixture_ids:
            old_grp = self._stage_config.get_group_for_fixture(fid)
            if old_grp:
                old_grp.member_ids.remove(fid)
                if len(old_grp.member_ids) < 2:
                    self._stage_config.remove_group(old_grp.id)

        # Use the centroid of the members as the group origin.
        positions = [obj.position for fid in fixture_ids if (obj := self._stage_config.get_object(fid)) is not None]
        n = max(len(positions), 1)
        cx = sum(p[0] for p in positions) / n
        cy = sum(p[1] for p in positions) / n
        cz = sum(p[2] for p in positions) / n

        group_id = self._stage_config.get_new_id("group")
        new_group = FixtureGroup(
            group_id=group_id, name=group_name, position=(cx, cy, cz), rotation=(0.0, 0.0, 0.0), member_ids=fixture_ids
        )
        self._stage_config.add_group(new_group)
        self._save_stage()
        self._editor_widget.refresh_list()

    def _on_remove_group(self, group_id: str) -> None:
        if self._stage_config.remove_group(group_id):
            self._save_stage()
            self._editor_widget.refresh_list()

    def _on_fixture_clicked(self, object_id: str) -> None:
        self._editor_widget.select_fixture_by_id(object_id)

    def _on_deselect_all(self) -> None:
        self._editor_widget.deselect_all()

    def _on_dmx_toggled(self, _enabled: bool) -> None:
        """React to the DMX Live checkbox; visibility decides whether we actually poll."""
        self._update_dmx_polling()

    def _update_dmx_polling(self) -> None:
        """Poll Fish for DMX frames only while live mode is on AND the visualizer is visible."""
        self._dmx_vis.enabled = self._editor_widget.dmx_live_enabled() and self.isVisible()

    def _on_dmx_updated(self) -> None:
        self._editor_widget.update_live_values()
        self._gl_widget.update()

    # Stage file persistence

    def _schedule_save(self) -> None:
        """Queue a debounced save of the stage file."""
        self._save_timer.start()

    def _save_stage(self) -> None:
        """Persist the stage file immediately and surface failures to the user.

        A message box is only shown when a previously working save starts
        failing, so a persistently broken target does not spam popups.
        """
        if self._stage_config.save():
            self._save_failed = False
            return
        if not self._save_failed:
            self._save_failed = True
            logger.error("Could not save stage file %s", self._stage_config.file_path)
            QtWidgets.QMessageBox.warning(
                self,
                "Stage",
                f"The stage file could not be saved:\n{self._stage_config.file_path}\n\n"
                "Your setup stays in memory. Check the log for details.",
            )
