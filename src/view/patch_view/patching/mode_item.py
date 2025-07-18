"""Widget of a Fixture Mode."""

from PySide6 import QtWidgets

import style
from model.ofl.fixture import Mode


class ModeItem(QtWidgets.QPushButton):
    """Widget of a Fixture Mode."""

    def __init__(self, mode: Mode) -> None:
        """Widget of a Fixture Mode."""
        super().__init__()
        self.setFixedSize(150, 100)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        manufacturer_label: QtWidgets.QLabel = QtWidgets.QLabel(str(mode["name"]), self)
        layout.addWidget(manufacturer_label)

        self.setStyleSheet(style.PATCH + "background-color: white;")
        self.setLayout(layout)
