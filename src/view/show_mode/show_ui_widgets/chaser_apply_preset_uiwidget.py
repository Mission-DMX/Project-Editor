"""Contains a UI Widget that applies chaser presets."""

from __future__ import annotations

from typing import override

from PySide6.QtWidgets import QDialog, QFormLayout, QListWidget, QPushButton, QSpinBox, QVBoxLayout, QWidget

from model import UIPage, UIWidget
from model.filter_data.chaser_model import ChaserConfig, ChaserModel
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem


class ChaserApplyPresetUIWidget(UIWidget):
    """UI Widget that applies chaser presets."""

    def __init__(self, parent_page: UIPage, configuration: dict[str, str] | None = None) -> None:
        """Initialize UI widget handler for provided filter page using provided configuration."""
        super().__init__(parent_page, configuration)
        self._pending_update: str | None = None

    def _construct_widget(self) -> QWidget:
        model = ChaserModel(self.parent.scene.get_filter_by_id(self.filter_ids[0]).filter_configurations)
        widget = QWidget()
        layout = QVBoxLayout()
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(list_widget)
        apply_button = QPushButton()
        apply_button.setText("Apply")
        apply_button.clicked.connect(lambda lw=list_widget: self._apply_preset_from_item(lw.selectedItems()[0]))
        layout.addWidget(apply_button)
        for preset in model.presets:
            item = AnnotatedListWidgetItem(list_widget)
            item.setText(preset.name)
            item.annotated_data = preset
            list_widget.addItem(item)
        widget.setLayout(layout)
        widget.setFixedWidth(int(self.configuration.get("width") or "64"))
        widget.setFixedHeight(int(self.configuration.get("height") or "64"))
        return widget

    def _apply_preset_from_item(self, item: AnnotatedListWidgetItem) -> None:
        if not isinstance(item, AnnotatedListWidgetItem):
            return
        preset = item.annotated_data
        if not isinstance(preset, ChaserConfig):
            return
        self._pending_update = preset.format_for_filter_str()
        self.push_update()

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        if self._pending_update is None:
            return []
        command_list = [("config", self._pending_update)]
        self._pending_update = None
        return command_list

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        w: QWidget = self._construct_widget()
        w.setParent(parent)
        return w

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        w: QWidget = self._construct_widget()
        w.setParent(parent)
        w.setEnabled(False)
        return w

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        w = ChaserApplyPresetUIWidget(new_parent, self.configuration)
        super().copy_base(w)
        return w

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        w = QWidget(parent)
        layout = QFormLayout()
        width_box = QSpinBox()
        width_box.setMinimum(64)
        width_box.setMaximum(16384)
        width_box.setValue(int(self.configuration.get("width") or "64"))
        width_box.valueChanged.connect(self._config_width_value_changed)
        layout.addRow("Width", width_box)
        height_box = QSpinBox()
        height_box.setMinimum(64)
        height_box.setMaximum(16384)
        height_box.setValue(int(self.configuration.get("height") or "64"))
        height_box.valueChanged.connect(self._config_height_value_changed)
        layout.addRow("Height", height_box)
        w.setLayout(layout)
        return w

    def _config_width_value_changed(self, new_value: int) -> None:
        # TODO implement live update (like macro buttons, refactor to get a size mixin)
        self.configuration["width"] = str(new_value)

    def _config_height_value_changed(self, new_value: int) -> None:
        # TODO implement live update (like macro buttons
        self.configuration["height"] = str(new_value)

