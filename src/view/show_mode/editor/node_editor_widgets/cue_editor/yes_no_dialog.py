# coding=utf-8
"""simple non-blocking Yes No Dialog"""

from collections.abc import Callable

from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QPushButton, QWidget


class YesNoDialog(QDialog):
    """simple non-blocking Yes No Dialog"""
    def __init__(self, parent: QWidget, question: str, success_action: Callable[[], None]) -> None:
        super().__init__(parent)
        self._layout = QFormLayout()
        self._layout.addRow(question, QLabel(""))
        self._yes_button = QPushButton("Yes")
        self._yes_button.clicked.connect(self._yes__button_pressed)
        self._no_button = QPushButton("No")
        self._no_button.clicked.connect(self._no_button_pressed)
        self._layout.addRow(self._yes_button, self._no_button)
        self.setLayout(self._layout)
        self._success_action = success_action
        self.open()

    def _yes__button_pressed(self) -> None:
        self.close()
        self._success_action()
        self.deleteLater()

    def _no_button_pressed(self) -> None:
        self.close()
        self.deleteLater()
