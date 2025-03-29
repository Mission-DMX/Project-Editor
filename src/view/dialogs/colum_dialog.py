# coding=utf-8
"""modify a colum of XTouch"""
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from model import ColorHSI
from model.broadcaster import Broadcaster
from model.control_desk import BankSet, ColorDeskColumn
from view.dialogs.temperature_dialog import TemperatureDialog


class ColumnDialog(QtWidgets.QDialog):
    """select how to modify a colum of XTouch"""

    def __init__(self, column: ColorDeskColumn, parent: object = None) -> None:
        super().__init__(parent)
        self._broadcaster = Broadcaster()
        self.setWindowTitle(f"Change Column {column.id}")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._column = column
        self.color_d = QtWidgets.QColorDialog()
        self.color_d.currentColorChanged.connect(self._select_color)
        self.temperature_d = TemperatureDialog(self._column)

        # self.colorD.finished.connect(self._select_color)
        # color_label = QtWidgets.QLabel(column.color.format_for_filter())
        color_picker = QtWidgets.QPushButton("pick Color")
        color_picker.clicked.connect(lambda: self._broadcaster.view_to_color.emit())
        self.color_d.finished.connect(lambda: self._broadcaster.view_leave_color.emit())

        temperature_picker = QtWidgets.QPushButton("pick Temperature")
        temperature_picker.clicked.connect(lambda: self._broadcaster.view_to_temperature.emit())
        self.temperature_d.finished.connect(lambda: self._broadcaster.view_leave_temperature.emit())

        color_layout = QtWidgets.QVBoxLayout()
        color_layout.addWidget(color_picker)
        color_layout.addWidget(temperature_picker)

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
        color = self.color_d.currentColor()
        self._column.color = ColorHSI(color.hue(), color.hslSaturationF(), color.toHsl().lightnessF())
        BankSet.push_messages_now()

    def _to_color(self):
        self.temperature_d.close()
        if not self.color_d.isVisible():
            self.color_d.show()
        else:
            self.color_d.close()

    def _to_temperature(self):
        self.color_d.close()
        if not self.temperature_d.isVisible():
            self.temperature_d.show()
        else:
            self.temperature_d.close()

    def _reject(self) -> None:
        self.color_d.close()
        self.temperature_d.close()
        del self.color_d
        del self.temperature_d
        self.reject()
