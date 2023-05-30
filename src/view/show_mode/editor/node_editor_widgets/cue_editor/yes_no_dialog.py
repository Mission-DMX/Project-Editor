from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QWidget, QFormLayout, QLabel, QPushButton


class YesNoDialog(QDialog):
    def __init__(self, parent: QWidget, success_action):
        super().__init__(parent)
        self._layout = QFormLayout()
        self._layout.addRow("Would you like to switch to live preview?", QLabel(""))
        self._yes_button = QPushButton("Yes")
        self._yes_button.clicked.connect(self._yes__button_pressed)
        self._no_button = QPushButton("No")
        self._no_button.clicked.connect(self._no_button_pressed)
        self._layout.addRow(self._yes_button, self._no_button)
        self.setLayout(self._layout)
        self._success_action = success_action
        self.open()

    def _yes__button_pressed(self):
        self.close()
        self._success_action()

    def _no_button_pressed(self):
        self.close()
