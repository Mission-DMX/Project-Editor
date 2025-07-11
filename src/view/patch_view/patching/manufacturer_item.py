"""Widget of a Manufacturer"""
from PySide6 import QtWidgets

import style
from model.ofl.manufacture import Manufacture


class ManufacturerItem(QtWidgets.QPushButton):
    """Widget of a Manufacturer"""

    def __init__(self, manufacturer: Manufacture) -> None:
        super().__init__()
        self.setFixedSize(150, 100)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        manufacturer_label: QtWidgets.QLabel = QtWidgets.QLabel(str(manufacturer["name"]), self)
        layout.addWidget(manufacturer_label)

        self.setStyleSheet(style.PATCH + "background-color: white;")
        self.setLayout(layout)
