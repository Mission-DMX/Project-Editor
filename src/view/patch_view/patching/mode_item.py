"""Widget of a Mode"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

import style

if TYPE_CHECKING:
    from model.ofl.ofl_fixture import FixtureMode


class ModeItem(QtWidgets.QPushButton):
    """Widget of a Fixture"""

    def __init__(self, mode: FixtureMode) -> None:
        super().__init__()
        self.setFixedSize(150, 100)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        manufacturer_label: QtWidgets.QLabel = QtWidgets.QLabel(mode.name, self)
        layout.addWidget(manufacturer_label)

        self.setStyleSheet(style.PATCH + "background-color: white;")
        self.setLayout(layout)
