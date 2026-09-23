"""Top-level widget of the stage visualizer.

Combines the 3D viewport, the editor panel and the DMX poller behind a
single QSplitter and relays signals between them.

"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, override

from PySide6 import QtCore, QtWidgets

from model.broadcaster import Broadcaster
from model.visualizer.dmx.dmx_parser import DmxParser, MovementRole, auto_detect_mapping, get_movement_range
from model.visualizer.stage.fixture_group import FixtureGroup
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

        logger.info("Stage loaded: %d objects", len(new_config.objects))

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
                ch_names = [ch.name for ch in device.fixture_channels]
                mapping = auto_detect_mapping(ch_names, MovementRole)
                new_obj.device_config = {
                    "movement": {
                        "universe": device.universe_id,
                        "start_channel": device.start_index,
                        "channel_count": device.channel_length,
                        "mapping": mapping,
                        "pan_tilt_range": get_movement_range(device),
                    }
                }
            except Exception as e:
                logger.warning("Could not auto-link device: %s", e)

        self._stage_config.add_object(new_obj)
        self._editor_widget.add_object_to_list(new_obj)

        self._gl_widget.makeCurrent()
        self._gl_widget.load_object(new_obj)
        self._gl_widget.doneCurrent()
        self._gl_widget.update()
        self._save_stage()

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
