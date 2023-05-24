# coding=utf-8
"""Widget of a Manufacturer"""
from PySide6 import QtWidgets

from Style import Style
from ofl.manufacture import Manufacture


class ManufacturerItem(QtWidgets.QPushButton):
    """Widget of a Manufacturer"""

    def __init__(self, manufacturer: Manufacture):
        super().__init__()
        self.setFixedSize(150, 100)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        manufacturer_label: QtWidgets.QLabel = QtWidgets.QLabel(str(manufacturer['name']), self)
        layout.addWidget(manufacturer_label)

        self.setStyleSheet(Style.PATCH + f"background-color: white;")
        self.setLayout(layout)
