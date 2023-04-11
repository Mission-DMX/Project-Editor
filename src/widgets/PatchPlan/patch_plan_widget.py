from PySide6 import QtWidgets, QtCore
from PySide6.examples.widgets.layouts.flowlayout.flowlayout import FlowLayout

from src.DMXModel import Universe
from widgets.PatchPlan.patch_item import PatchItem


class PatchPlanWidget(QtWidgets.QScrollArea):
    """TODO Hier soll ein selbst Floating Widget hin"""
    def __init__(self, universe: Universe, parent=None):
        super().__init__(parent=parent)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QtWidgets.QWidget()
        container_layout = FlowLayout()

        for i, channel in enumerate(universe.channels):
            container_layout.addWidget(PatchItem(channel, universe))

        container.setLayout(container_layout)

        self.setWidgetResizable(True)
        self.setWidget(container)


