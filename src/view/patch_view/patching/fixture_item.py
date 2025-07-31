"""Widget of a Fixture"""
from PySide6 import QtWidgets

import style
from model.ofl.fixture import Fixture


class FixtureItem(QtWidgets.QPushButton):
    """Widget of a Fixture"""

    def __init__(self, fixture: Fixture) -> None:
        super().__init__()
        self.setFixedSize(150, 100)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        manufacturer_label: QtWidgets.QLabel = QtWidgets.QLabel(str(fixture["name"]), self)
        layout.addWidget(manufacturer_label)

        self.setStyleSheet(style.PATCH + "background-color: white;")
        self.setLayout(layout)
