# coding=utf-8
"""Widget of a Fixture"""
from PySide6 import QtWidgets

from Style import Style
from model.ofl.fixture import Fixture


class FixtureItem(QtWidgets.QPushButton):
    """Widget of a Fixture"""

    def __init__(self, fixture: Fixture):
        super().__init__()
        self.setFixedSize(150, 100)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        manufacturer_label: QtWidgets.QLabel = QtWidgets.QLabel(str(fixture['name']), self)
        layout.addWidget(manufacturer_label)

        self.setStyleSheet(Style.PATCH + f"background-color: white;")
        self.setLayout(layout)
