from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QWidget, QHBoxLayout, QTabWidget, QFormLayout, \
    QLineEdit, QTextEdit

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model import BoardConfiguration


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None, show: "BoardConfiguration"):
        super().__init__(parent)
        self.setWindowTitle("Setting: " + show.show_name)
        exit_buttons = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Apply |
                        QDialogButtonBox.StandardButton.Cancel)

        self._category_tab_bar = QTabWidget(self)
        self._general_settings_tab = QWidget(self._category_tab_bar)
        general_layout = QFormLayout()
        self.show_file_tb = QLineEdit(self._general_settings_tab)
        general_layout.addRow("Show File Name: ", self.show_file_tb)
        self.show_notes_tb = QTextEdit(self._general_settings_tab)
        self._general_settings_tab.setLayout(general_layout)
        self._category_tab_bar.addTab(self._general_settings_tab, "General")

        self.buttonBox = QDialogButtonBox(exit_buttons)
        self.buttonBox.accepted.connect(self.ok_button_pressed)
        self.buttonBox.rejected.connect(self.cancle_button_pressed)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self._category_tab_bar)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.show = show

    @property
    def show(self) -> "BoardConfiguration":
        return self._show

    @show.setter
    def show(self, new_show: "BoardConfiguration"):
        self._show = new_show
        self.show_file_tb.setText(new_show.show_name)
        self.show_notes_tb.setText(new_show.notes)

    def apply(self):
        self._show.show_name = self.show_file_tb.text()
        self._show.notes = self.show_notes_tb.toPlainText()

    def ok_button_pressed(self):
        self.apply()
        self.accept()

    def cancle_button_pressed(self):
        self.reject()


