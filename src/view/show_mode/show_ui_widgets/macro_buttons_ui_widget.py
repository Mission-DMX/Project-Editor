"""Provides UI widget to allow quick execution of macros by user."""

from __future__ import annotations

import json
import os
from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QWidget,
)

from model import UIWidget
from utility import resource_path
from view.action_setup_view._command_insertion_dialog import escape_argument
from view.show_mode.editor.editor_tab_widgets.ui_widget_editor._widget_holder import UIWidgetHolder
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem
from view.utility_widgets.box_grid_renderer import BoxGridItem, BoxGridRenderer

if TYPE_CHECKING:
    from model import UIPage


class _AddMacroActionDialog(QDialog):
    def __init__(self, ui_widget: MacroButtonUIWidget, button_list: QListWidget, update_button: QPushButton) -> None:
        super().__init__(parent=button_list)
        self._ui_widget = ui_widget
        self._update_button = update_button
        self._button_list = button_list
        self.setModal(True)
        self.setWindowTitle("Add Macro")
        layout = QFormLayout()
        self._command_tb = QLineEdit(self)
        self._macro_combo_box = QComboBox(self)
        self._macro_combo_box.setEditable(False)
        self._reload_macro_cb()
        self._macro_combo_box.currentIndexChanged.connect(self._populate_command_from_macro)
        layout.addRow("Macro: ", self._macro_combo_box)
        # TODO add New Macro Button
        layout.addRow("Command: ", self._command_tb)
        self._text_tb = QLineEdit(self)
        layout.addRow("Display Text: ", self._text_tb)
        # TODO add Icon selection from show media storage
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._button_box.accepted.connect(self._ok_button_pressed)
        self._button_box.rejected.connect(self._cancel_button_pressed)
        layout.addWidget(self._button_box)
        self.setLayout(layout)
        self.setMinimumWidth(400)
        self.show()

    def _reload_macro_cb(self) -> None:
        self._macro_combo_box.clear()
        for m in self._ui_widget.parent.scene.board_configuration.macros:
            self._macro_combo_box.addItem(m.name, m)
        self._populate_command_from_macro()

    def _populate_command_from_macro(self) -> None:
        if data := self._macro_combo_box.currentData():
            self._command_tb.setText(f"macro exec {escape_argument(data.name)}")

    def _ok_button_pressed(self) -> None:
        model = json.loads(self._ui_widget.configuration.get("items") or "[]")
        model.append({"text": self._text_tb.text(), "command": self._command_tb.text()})
        self._ui_widget.configuration["items"] = json.dumps(model)
        self._ui_widget._refresh_config_macro_list(self._button_list, update_button=self._update_button)
        self.close()

    def _cancel_button_pressed(self) -> None:
        self.close()


class _MacroListWidget(QWidget):
    _NO_ICON = QIcon(resource_path(os.path.join("resources", "icons", "missing-image.svg")))

    def __init__(self, parent: QListWidget, item_def: dict[str, str], index: int, update_button: QPushButton) -> None:
        super().__init__(parent)
        self._item_def = item_def
        self._update_button: QPushButton = update_button
        layout = QHBoxLayout()
        layout.addWidget(QLabel(str(index)))
        self._icon_bt = QPushButton(self)
        self._icon_bt.setIcon(self._NO_ICON)
        layout.addWidget(self._icon_bt)
        layout.addStretch()
        self._text_tb = QLineEdit(self)
        self._text_tb.setText(item_def["text"])
        self._text_tb.textChanged.connect(self._text_changed)
        layout.addWidget(self._text_tb)
        layout.addStretch()
        self._command_tb = QLineEdit(self)
        self._command_tb.setText(item_def["command"])
        self._command_tb.textChanged.connect(self._command_changed)
        layout.addWidget(self._command_tb)
        self.setLayout(layout)
        # TODO implement icon display and changing functionality

    def _text_changed(self, text: str) -> None:
        self._item_def["text"] = text
        self._update_button.setEnabled(True)

    def _command_changed(self, text: str) -> None:
        self._item_def["command"] = text
        self._update_button.setEnabled(True)

    @property
    def item_def(self) -> dict[str, str]:
        return self._item_def


class MacroButtonUIWidget(UIWidget):
    """Widget displaying button selection for execution of macros."""

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize widget using configuration and parent ui page."""
        super().__init__(parent, configuration)
        self._latest_config_widget: QWidget | None = None
        self._latest_player_widget: QWidget | None = None

        if not self.configuration.get("items"):
            self.configuration["items"] = "[]"
        if not self.configuration.get("width"):
            self.configuration["width"] = "128"
        if not self.configuration.get("height"):
            self.configuration["height"] = "64"
        self._latest_config_widget: BoxGridRenderer | None = None
        from controller.cli.cli_context import CLIContext
        from controller.network import NetworkManager

        self._context = CLIContext(parent.scene.board_configuration, NetworkManager(), False)
        self._logger = getLogger(f"{parent.title} macro_button_returns")

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        return []

    def _construct_widget(self) -> QWidget:
        w = BoxGridRenderer()
        w.setFixedWidth(max(int(self.configuration.get("width") or "64"), w.minimumWidth()))
        w.setFixedHeight(max(int(self.configuration.get("height") or "64"), w.minimumHeight()))
        self._populate_button_items(w)
        return w

    def _populate_button_items(self, w: BoxGridRenderer) -> None:
        w.clear()
        for item_def in json.loads(self.configuration.get("items") or "[]"):
            item = BoxGridItem(w)
            item.text = item_def["text"]
            item.data = item_def["command"]
            item.clicked.connect(self._exec_command)
            w.add_item(item)

    def _exec_command(self, command: str) -> None:
        if not command:
            return
        if not self._context.exec_command(command):
            self._mbox = QMessageBox()
            self._mbox.setWindowTitle("Command failed.")
            self._mbox.setText("Please check the log for its output.")
            self._mbox.show()
        self._logger.info(self._context.return_text)
        self._context.return_text = ""

    @override
    def get_player_widget(self, parent: QWidget) -> QWidget:
        self._latest_player_widget = self._construct_widget()
        return self._latest_player_widget

    @override
    def get_configuration_widget(self, parent: QWidget) -> QWidget:
        self._latest_config_widget = self._construct_widget()
        return self._latest_config_widget

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        w = MacroButtonUIWidget(new_parent, self.configuration.copy())
        self.copy_base(w)
        return w

    def _refresh_config_macro_list(self, config_list: QListWidget, update_button: QPushButton) -> None:
        config_list.clear()
        model = json.loads(self.configuration["items"])
        for i, item_def in enumerate(model):
            item = AnnotatedListWidgetItem(config_list)
            item.annotated_data = item_def
            item_widget = _MacroListWidget(config_list, item_def, i, update_button)
            item.setSizeHint(item_widget.sizeHint())
            config_list.addItem(item)
            config_list.setItemWidget(item, item_widget)
        if self._latest_config_widget is not None:
            self._populate_button_items(self._latest_config_widget)

    @override
    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        w = QWidget()
        w.setMinimumWidth(600)
        w.setMinimumHeight(800)
        form_layout = QFormLayout()
        width_box = QSpinBox()
        width_box.setMinimum(64)
        width_box.setMaximum(16384)
        width_box.setValue(int(self.configuration.get("width") or "64"))
        width_box.valueChanged.connect(self._config_width_value_changed)
        form_layout.addRow("Width", width_box)
        height_box = QSpinBox()
        height_box.setMinimum(64)
        height_box.setMaximum(16384)
        height_box.setValue(int(self.configuration.get("height") or "64"))
        height_box.valueChanged.connect(self._config_height_value_changed)
        form_layout.addRow("Height", height_box)
        add_macro_button = QPushButton("Add macro")
        form_layout.addWidget(add_macro_button)
        button_list = QListWidget()
        form_layout.addWidget(button_list)
        update_button = QPushButton("Update Buttons")
        update_button.setEnabled(False)
        update_button.clicked.connect(lambda: self._update_properties(button_list, update_button))
        form_layout.addWidget(update_button)
        self._refresh_config_macro_list(button_list, update_button)
        add_macro_button.clicked.connect(lambda: _AddMacroActionDialog(self, button_list, update_button))
        w.setLayout(form_layout)
        return w

    def _update_properties(self, button_list: QListWidget, update_button: QPushButton) -> None:
        model = json.loads(self.configuration["items"])
        for i, item_def in enumerate(model):
            item_def.update(button_list.itemWidget(button_list.item(i)).item_def)
        self.configuration["items"] = json.dumps(model)
        if self._latest_config_widget is not None:
            self._populate_button_items(self._latest_config_widget)
        if self._latest_player_widget is not None:
            self._populate_button_items(self._latest_player_widget)
        update_button.setEnabled(False)

    def _config_width_value_changed(self, new_value: int) -> None:
        for widget in [self._latest_player_widget, self._latest_config_widget]:
            if widget is not None:
                widget.setFixedWidth(new_value)
                wh = widget.parent()
                if isinstance(wh, UIWidgetHolder):
                    wh.update_size()
        self.configuration["width"] = str(new_value)

    def _config_height_value_changed(self, new_value: int) -> None:
        for widget in [self._latest_player_widget, self._latest_config_widget]:
            if widget is not None:
                widget.setFixedHeight(new_value)
                wh = widget.parent()
                if isinstance(wh, UIWidgetHolder):
                    wh.update_size()
        self.configuration["height"] = str(new_value)
