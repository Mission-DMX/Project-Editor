# coding=utf-8
"""patch Plan Widget for one Universe"""
from PySide6 import QtWidgets, QtCore
from PySide6.examples.widgets.layouts.flowlayout.flowlayout import FlowLayout

from model.patching_universe import PatchingUniverse
from view.patching.patch_item import PatchItem


class PatchPlanWidget(QtWidgets.QScrollArea):
    """Patch Plan Widget for one Universe"""

    def __init__(self, universe: PatchingUniverse, parent=None):
        super().__init__(parent=parent)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._patch_items: list[PatchItem] = []

        container = QtWidgets.QWidget()
        container_layout = FlowLayout()

        for i, channel in enumerate(universe.patching):
            item = PatchItem(channel, universe)
            container_layout.addWidget(item)
            self._patch_items.append(item)

        container.setLayout(container_layout)

        self.setWidgetResizable(True)
        self.setWidget(container)

    def update_patching(self, index: int) -> None:
        """
        update the Patching for a defined item
        Args:
            index: index of updater patch item
        """
        self._patch_items[index].update_patching()
