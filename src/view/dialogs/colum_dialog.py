# coding=utf-8
"""modify a colum of XTouch"""
from PySide6 import QtWidgets

from model import ColorHSI
from model.broadcaster import Broadcaster
from model.control_desk import ColorDeskColumn, BankSet


class ColumnDialog(QtWidgets.QDialog):
    def __init__(self, column: ColorDeskColumn, parent: object = None) -> None:
        super().__init__(parent)
        self._broadcaster = Broadcaster()
        self.setWindowTitle(f"Change Column {column.id}")
        self._column = column
        self.colorD = QtWidgets.QColorDialog()
        self.colorD.currentColorChanged.connect(self._select_color)

        # self.colorD.finished.connect(self._select_color)
        # color_label = QtWidgets.QLabel(column.color.format_for_filter())
        color_picker = QtWidgets.QPushButton("pick Color")
        color_picker.clicked.connect(lambda: self.colorD.show())

        color_layout = QtWidgets.QVBoxLayout()
        # color_layout.addWidget(color_label)
        color_layout.addWidget(color_picker)

        tab_widget = QtWidgets.QTabWidget()
        color_widget = QtWidgets.QWidget()
        color_widget.setLayout(color_layout)
        tab_widget.addTab(color_widget, "color")

        button = QtWidgets.QPushButton("ok")
        button.clicked.connect(self._accept)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tab_widget)
        layout.addWidget(button)
        self.setLayout(layout)

    def _select_color(self):
        color = self.colorD.currentColor()
        self._column.color = ColorHSI(color.hue(), color.hslSaturationF(), color.toHsl().lightnessF())
        BankSet.push_messages_now()

    def _accept(self) -> None:
        self._broadcaster.view_leave_colum_select.emit()
        self.accept()
