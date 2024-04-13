# coding=utf-8
"""patch Plan Widget for one Universe"""
from PySide6 import QtCore, QtWidgets

from model.patching_universe import PatchingUniverse
from view.patch_mode.patch_plan.patch_plan_item import PatchItem
from layouts.flow_layout import FlowLayout


class PatchPlanWidget(QtWidgets.QScrollArea):
    """Patch Plan Widget for one Universe"""

    def __init__(self, universe: PatchingUniverse, parent=None):
        super().__init__(parent=parent)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._patch_items: list[PatchItem] = []

        container = QtWidgets.QWidget()
        container_layout = FlowLayout()

        for channel in universe.patching:
            item = PatchItem(channel, universe)
            container_layout.addWidget(item)
            self._patch_items.append(item)

        container.setLayout(container_layout)

        self.setWidgetResizable(True)
        self.setWidget(container)
