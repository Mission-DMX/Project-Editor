# coding=utf-8
"""Widget of a Mode"""
from PySide6 import QtWidgets

from Style import Style
from controller.ofl.fixture import Mode


class ModeItem(QtWidgets.QPushButton):
    """Widget of a Fixture"""

    def __init__(self, mode: Mode):
        super().__init__()
        self.setFixedSize(150, 100)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        manufacturer_label: QtWidgets.QLabel = QtWidgets.QLabel(str(mode['name']), self)
        layout.addWidget(manufacturer_label)

        self.setStyleSheet(Style.PATCH + f"background-color: white;")
        self.setLayout(layout)
