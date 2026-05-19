"""Contains a UI widget to edit chaser configs live."""

from __future__ import annotations

from typing import override

from PySide6.QtWidgets import QDialog, QLabel, QWidget

from model import UIPage, UIWidget
from model.filter_data.chaser_model import ChaserConfig, ChaserModel
from view.show_mode.editor.node_editor_widgets.chaser_editor.layer_config_widget import ChaserLayerConfigWidget


class ChaserCreateConfigUIWidget(UIWidget):
    """UI widget to edit chaser configs live."""

    def __init__(self, parent_page: UIPage, configuration: dict[str, str] | None = None) -> None:
        """Initialize UI widget handler for provided filter page using provided configuration."""
        super().__init__(parent_page, configuration)
        self._pending_update: str | None = None

    def _construct_widget(self, parent: QWidget | None) -> QWidget:
        model = ChaserModel(self.parent.scene.get_filter_by_id(self.filter_ids[0]).filter_configurations)
        w = ChaserLayerConfigWidget(model, parent, "Apply")
        w.config = ChaserConfig("")
        w.set_test_method(self._apply_configuration)
        return w

    def _apply_configuration(self, config: ChaserConfig) -> None:
        if config is None:
            return
        self._pending_update = config.format_for_filter_str()

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        if self._pending_update is None:
            return []
        command_list = [("config", self._pending_update)]
        self._pending_update = None
        return command_list

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        w: QWidget = self._construct_widget(parent)
        return w

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        w: QWidget = self._construct_widget(parent)
        w.setEnabled(False)
        return w

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        w = ChaserCreateConfigUIWidget(new_parent, self.configuration)
        super().copy_base(w)
        return w

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        return QLabel("Nothing to configure here.")
