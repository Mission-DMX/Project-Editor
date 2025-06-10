from typing import TYPE_CHECKING

from model import UIWidget

from PySide6.QtWidgets import QWidget, QFormLayout, QSpinBox, QPushButton, QListWidget, QDialog

if TYPE_CHECKING:
    from model import UIPage


class _AddMacroActionDialog(QDialog):
    def __init__(self, ui_widget: "MacroButtonUIWidget", button_list: QListWidget):
        super().__init__(parent=button_list)
        self._ui_widget = ui_widget
        self._button_list = button_list
        self.setModal(True)
        self.setWindowTitle("Add Macro")
        # TODO add button list for OK and Cancel
        # TODO add Macro selection (combo box)
        # TODO add New Macro Button
        # TODO add Text Box for manual command insertion update
        # TODO add Text Box for Button Text
        # TODO add Icon selection from show media storage
        self.show()


class MacroButtonUIWidget(UIWidget):
    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
        super().__init__(parent, configuration)

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
        pass  # TODO add items containing Text, Icon and CLI command (with appropriate font)

    def get_config_dialog_widget(self, parent: "QWidget") -> "QWidget":
        w = QWidget()
        l = QFormLayout()
        width_box = QSpinBox()
        width_box.setMinimum(64)
        width_box.setValue(int(self.configuration["width"]))
        l.addRow("Width", width_box)
        height_box = QSpinBox()
        height_box.setMinimum(64)
        height_box.setValue(int(self.configuration["height"]))
        l.addRow("Height", height_box)
        add_macro_button = QPushButton("Add macro")
        l.addWidget(add_macro_button)
        button_list = QListWidget()
        self.refresh_config_macro_list(button_list)
        l.addWidget(button_list)
        add_macro_button.clicked.connect(lambda: _AddMacroActionDialog(self, button_list))
        w.setLayout(l)
        return w