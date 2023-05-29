# coding=utf-8
"""dialog for change of Temperature"""
import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui

from model import ColorHSI
from model.control_desk import ColorDeskColumn, BankSet


class TemperatureDialog(QtWidgets.QDialog):
    """dialog for change of Temperature"""

    def __init__(self, column: ColorDeskColumn, parent: object = None) -> None:
        super().__init__(parent)
        self._column = column
        self.temperature = QtWidgets.QSpinBox(self)
        self.temperature.setMaximum(40000)
        self.temperature.setMinimum(1000)
        self.temperature.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.ok_button = QtWidgets.QPushButton("ok")
        self.ok_button.clicked.connect(self._calculate_color)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("select Temperature:"))
        layout.addWidget(self.temperature)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def _calculate_color(self):
        temperature = float(self.temperature.text()) / 100
        color = QtGui.QColor()
        color.setRed(int(_calculate_red(temperature)))
        color.setGreen(int(_calculate_green(temperature)))
        color.setBlue(int(_calculate_blue(temperature)))
        self._column.color = ColorHSI(color.hue(), color.hslSaturationF(), color.toHsl().lightnessF())
        BankSet.push_messages_now()
        self.reject()


def _calculate_red(temperature: float) -> float:
    if temperature <= 66:
        return 255.0
    return _col_check(329.698727446 * pow(temperature - 60, -0.1332047592))


def _calculate_green(temperature: float) -> float:
    if temperature <= 60:
        return _col_check(99.4708025861 * np.log(temperature) - 161.1195681661)
    else:
        return _col_check(288.1221695283 * pow(temperature - 60, -0.0755148492))


def _calculate_blue(temperature: float) -> float:
    if temperature >= 66:
        return 255.0
    if temperature < 19:
        return 0
    return _col_check(138.5177312231 * np.log(temperature - 10) - 305.0447927307)


def _col_check(color_part: float) -> int:
    if color_part < 0:
        return 0
    if color_part > 255:
        return 255
    return int(color_part)

# Set Temperature = Temperature \ 100
