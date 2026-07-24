"""Top-level widget of the stage visualizer.

Combines the 3D viewport, the editor panel and the DMX poller behind a
single QSplitter and relays signals between them.

"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from model.broadcaster import Broadcaster
from model.dmx.dmx_visualizer import MOVEMENT_ROLES, DmxVisualizer, auto_detect_mapping
from model.stage import FixtureGroup, StageConfig, backup_stage_file, get_default_stage_path
from view.visualizer.stage_editor_widget import StageEditorWidget
from view.visualizer.stage_gl_widget import Stage3DWidget

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from model import BoardConfiguration
    from model.ofl.fixture import UsedFixture

logger = getLogger(__name__)


class StageVisualizerWidget(QtWidgets.QSplitter):
    """Horizontal split: 3D viewport on the left, editor panel on the right."""

    def __init__(self, board_configuration: BoardConfiguration, parent: QWidget | None = None) -> None:
        """Initialize using provided show file and parent object."""
        super().__init__(parent)
        self._broadcaster = Broadcaster()
        self._board_configuration = board_configuration

        self.setOrientation(QtCore.Qt.Orientation.Horizontal)

        stage_path = get_default_stage_path()
        logger.info("Loading stage from %s", stage_path)
        self._stage_config = StageConfig(stage_path)

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

        self._dmx_vis = DmxVisualizer(
            self._stage_config,
            board_configuration=board_configuration,
            parent=self,
        )
        self._dmx_vis.fixtures_updated.connect(self._on_dmx_updated)

        # Refresh fixture list when the show file changes.
        self._broadcaster.show_file_loaded.connect(self._refresh_fixtures)
        self._broadcaster.show_file_path_changed.connect(lambda _: self._refresh_fixtures())
        self._broadcaster.connection_state_updated.connect(
            lambda connected: QtCore.QTimer.singleShot(500, self._refresh_fixtures)
            if connected else None)
        self._broadcaster.add_fixture.connect(lambda _fix: self._refresh_fixtures())

        self._broadcaster.application_closing.connect(self._on_app_closing)

    def _on_app_closing(self) -> None:
        self._stage_config.save()
        logger.info("Stage saved to %s", self._stage_config.file_path)

    def load_stage_file(self) -> None:
        """Opens a file dialog to query a stage file and loads it."""
        # FIXME this is a blocking UI call.
        from model.stage import STAGE_DIR
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Stagefile", STAGE_DIR,
            "Stage Files (*.yaml *.yml);;All Files (*)")
        if not path:
            return

        backup = backup_stage_file(self._stage_config.file_path)
        if backup:
            logger.info("Current stage backed up to %s", backup)

        self._reload_stage(path)

    def save_stage_file(self) -> None:
        """Displays a save file dialog and saves the current stage setup into a stage file."""
        from model.stage import STAGE_DIR
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Stagefile", STAGE_DIR,
            "Stage Files (*.yaml *.yml);;All Files (*)")
        if not path:
            return
        self._stage_config.save_to(path)
        logger.info("Stage saved to %s", path)

    def _reload_stage(self, new_path: str) -> None:
        logger.info("Loading new stage: %s", new_path)

        new_config = StageConfig(new_path)
        new_config.save_to(get_default_stage_path())
        new_config.file_path = get_default_stage_path()

        self._stage_config = new_config
        self._dmx_vis._stage_config = new_config

        self._gl_widget.makeCurrent()
        self._gl_widget._stage_config = new_config
        self._gl_widget._load_all_objects()
        self._gl_widget.doneCurrent()
        self._gl_widget.update()

        self._editor_widget._stage_config = new_config
        self._editor_widget.refresh_list()

        logger.info("Stage loaded: %d objects", len(new_config.objects))

    def _get_fixtures(self) -> list[UsedFixture]:
        try:
            return list(self._board_configuration.fixtures)
        except Exception:
            return []

    def _refresh_fixtures(self) -> None:
        self._editor_widget._used_fixtures = self._get_fixtures()

    def _on_add_object(self, fixture_key: str, name: str, device: UsedFixture) -> None:
        new_id = self._stage_config.get_new_id(fixture_key)
        try:
            from model.stage import create_object_from_key
            new_obj = create_object_from_key(fixture_key, new_id, name)
        except Exception as e:
            logger.error("Failed to create object: %s", e)
            return

        # Auto-link the selected DMX device, if any.
        if device is not None:
            try:
                ch_names = [ch.name for ch in device.fixture_channels]
                mapping = auto_detect_mapping(ch_names, MOVEMENT_ROLES)
                new_obj.device_config = {
                    "movement": {
                        "universe": device.universe_id,
                        "start_channel": device.start_index,
                        "channel_count": device.channel_length,
                        "mapping": mapping,
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
        self._stage_config.save()

    def _on_remove_object(self, object_id: str) -> None:
        obj = self._stage_config.remove_object(object_id)
        if not obj:
            return
        self._editor_widget.remove_object_from_list(object_id)
        self._gl_widget.makeCurrent()
        self._gl_widget.remove_object(obj)
        self._gl_widget.doneCurrent()
        self._gl_widget.update()
        self._stage_config.save()
        self._editor_widget.refresh_list()

    def _on_object_changed(self, object_id: str) -> None:
        self._gl_widget.update()
        self._stage_config.save()

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
        positions = [self._stage_config.get_object(fid).position
                     for fid in fixture_ids
                     if self._stage_config.get_object(fid)]
        n = max(len(positions), 1)
        cx = sum(p[0] for p in positions) / n
        cy = sum(p[1] for p in positions) / n
        cz = sum(p[2] for p in positions) / n

        group_id = self._stage_config.get_new_id("group")
        new_group = FixtureGroup(
            group_id=group_id, name=group_name,
            position=(cx, cy, cz), rotation=(0.0, 0.0, 0.0),
            member_ids=fixture_ids)
        self._stage_config.add_group(new_group)
        self._stage_config.save()
        self._editor_widget.refresh_list()

    def _on_remove_group(self, group_id: str) -> None:
        if self._stage_config.remove_group(group_id):
            self._stage_config.save()
            self._editor_widget.refresh_list()

    def _on_fixture_clicked(self, object_id: str) -> None:
        self._editor_widget.select_fixture_by_id(object_id)

    def _on_deselect_all(self) -> None:
        self._editor_widget.deselect_all()

    def _on_dmx_toggled(self, enabled: bool) -> None:
        self._dmx_vis.enabled = enabled

    def _on_dmx_updated(self) -> None:
        self._editor_widget.update_live_values()
