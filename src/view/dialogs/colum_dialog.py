# coding=utf-8
"""modify a colum of XTouch"""
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from model import ColorHSI
from model.broadcaster import Broadcaster
from model.control_desk import ColorDeskColumn, BankSet
from view.dialogs.temperature_dialog import TemperatureDialog


class ColumnDialog(QtWidgets.QDialog):
    """select how to modify a colum of XTouch"""

    def __init__(self, column: ColorDeskColumn, parent: object = None) -> None:
        super().__init__(parent)
        self._broadcaster = Broadcaster()
        self.setWindowTitle(f"Change Column {column.id}")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._column = column
        self.colorD = QtWidgets.QColorDialog()
        self.colorD.currentColorChanged.connect(self._select_color)
        self.temperaturD = TemperatureDialog(self._column)

        # self.colorD.finished.connect(self._select_color)
        # color_label = QtWidgets.QLabel(column.color.format_for_filter())
        color_picker = QtWidgets.QPushButton("pick Color")
        color_picker.clicked.connect(lambda: self._broadcaster.view_to_color.emit())
        self.colorD.finished.connect(lambda: self._broadcaster.view_leave_color.emit())

        temperatur_picker = QtWidgets.QPushButton("pick Temperature")
        temperatur_picker.clicked.connect(lambda: self._broadcaster.view_to_temperature.emit())
        self.temperaturD.finished.connect(lambda: self._broadcaster.view_leave_temperature.emit())

        color_layout = QtWidgets.QVBoxLayout()
        color_layout.addWidget(color_picker)
        color_layout.addWidget(temperatur_picker)

        color_widget = QtWidgets.QWidget()
        color_widget.setLayout(color_layout)

        button = QtWidgets.QPushButton("close")
        button.clicked.connect(lambda: self._broadcaster.view_leave_colum_select.emit())
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(color_widget)
        layout.addWidget(button)
        self.setLayout(layout)
        self._broadcaster.view_leave_colum_select.connect(self._reject)
        self._broadcaster.view_change_colum_select.connect(self._reject)
        self._broadcaster.view_to_color.connect(self._to_color)
        self._broadcaster.view_to_temperature.connect(self._to_temperature)

    def _select_color(self):
        color = self.colorD.currentColor()
        self._column.color = ColorHSI(color.hue(), color.hslSaturationF(), color.toHsl().lightnessF())
        BankSet.push_messages_now()

    def _to_color(self):
        self.temperaturD.close()
        if not self.colorD.isVisible():
            self.colorD.show()
        else:
            self.colorD.close()

    def _to_temperature(self):
        self.colorD.close()
        if not self.temperaturD.isVisible():
            self.temperaturD.show()
        else:
            self.temperaturD.close()

    def _reject(self) -> None:
        self.colorD.close()
        self.temperaturD.close()
        del self.colorD
        del self.temperaturD
        self.reject()
