import json
import os
from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QPushButton, QSpinBox, QWidget)

from model import UIWidget
from utility import resource_path
from view.action_setup_view._command_insertion_dialog import escape_argument
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

if TYPE_CHECKING:
    from model import UIPage


class _AddMacroActionDialog(QDialog):
    def __init__(self, ui_widget: "MacroButtonUIWidget", button_list: QListWidget):
        super().__init__(parent=button_list)
        self._ui_widget = ui_widget
        self._button_list = button_list
        self.setModal(True)
        self.setWindowTitle("Add Macro")
        layout = QFormLayout()
        self._macro_combo_box = QComboBox(self)
        self._macro_combo_box.setEditable(False)
        self._reload_macro_cb()
        self._macro_combo_box.currentIndexChanged.connect(self._populate_command_from_macro)
        layout.addRow("Macro: ", self._macro_combo_box)
        # TODO add New Macro Button
        self._command_tb = QLineEdit(self)
        layout.addRow("Command: ", self._macro_combo_box)
        self._text_tb = QLineEdit(self)
        layout.addRow("Display Text: ", self._macro_combo_box)
        # TODO add Icon selection from show media storage
        self._button_box = QDialogButtonBox((QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel))
        self._button_box.accepted.connect(self._ok_button_pressed)
        self._button_box.rejected.connect(self._cancel_button_pressed)
        layout.addWidget(self._button_box)
        self.setLayout(layout)
        self.setMinimumWidth(400)
        self.show()

    def _reload_macro_cb(self):
        self._macro_combo_box.clear()
        for m in self._ui_widget.parent.scene.board_configuration.macros:
            self._macro_combo_box.addItem(m.name, m)
        self._populate_command_from_macro()

    def _populate_command_from_macro(self):
        if data := self._macro_combo_box.currentData():
            self._command_tb.setText(f"macro exec {escape_argument(data.name)}")

    def _ok_button_pressed(self):
        model = json.loads(self._ui_widget.configuration.get("items") or "[]")
        model.append({
            "text": self._command_tb.text(),
            "command": self._command_tb.text()
        })
        self._ui_widget.configuration["items"] = json.dumps(model)
        self._ui_widget.refresh_config_macro_list(self._button_list)
        self.close()

    def _cancel_button_pressed(self):
        self.close()


class _MacroListWidget(QWidget):

    _NO_ICON = QIcon(resource_path(os.path.join("resources", "icons", "missing-image.svg")))

    def __init__(self, parent: QListWidget, item_def: dict[str, str], index: int):
        super().__init__(parent)
        self._item_def = item_def
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

    def _text_changed(self, text: str):
        self._item_def["text"] = text

    def _command_changed(self, text: str):
        self._item_def["text"] = text


class MacroButtonUIWidget(UIWidget):
    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
        super().__init__(parent, configuration)
        if not self.configuration.get("items"):
            self.configuration["items"] = "[]"
        if not self.configuration.get("width"):
            self.configuration["width"] = "128"
        if not self.configuration.get("height"):
            self.configuration["height"] = "64"

    def generate_update_content(self) -> list[tuple[str, str]]:
        return []

    def _construct_widget(self) -> "QWidget":
        return QWidget()  # TODO replace with BoxGridRenderer

    def get_player_widget(self, parent: "QWidget") -> "QWidget":
        return self._construct_widget()

    def get_configuration_widget(self, parent: "QWidget") -> "QWidget":
        return self._construct_widget()

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        w = MacroButtonUIWidget(new_parent, self.configuration.copy())
        self.copy_base(w)
        return w

    def refresh_config_macro_list(self, config_list: QListWidget):
        config_list.clear()
        model = json.loads(self.configuration["items"])
        i = 0
        for item_def in model:
            item = AnnotatedListWidgetItem(config_list)
            item.annotated_data = item_def
            config_list.addItem(item)
            item_widget = _MacroListWidget(config_list, item_def, i)
            config_list.setItemWidget(item, item_widget)
            item.setSizeHint(item.sizeHint())
            i += 1

    def get_config_dialog_widget(self, parent: "QWidget") -> "QWidget":
        w = QWidget()
        l = QFormLayout()
        width_box = QSpinBox()
        width_box.setMinimum(64)
        width_box.setValue(int(self.configuration.get("width") or "64"))
        l.addRow("Width", width_box)
        height_box = QSpinBox()
        height_box.setMinimum(64)
        height_box.setValue(int(self.configuration.get("height") or "64"))
        l.addRow("Height", height_box)
        add_macro_button = QPushButton("Add macro")
        l.addWidget(add_macro_button)
        button_list = QListWidget()
        self.refresh_config_macro_list(button_list)
        l.addWidget(button_list)
        add_macro_button.clicked.connect(lambda: _AddMacroActionDialog(self, button_list))
        w.setLayout(l)
        return w