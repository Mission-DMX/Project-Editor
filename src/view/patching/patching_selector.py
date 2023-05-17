# coding=utf-8
"""selector for Patching witch holds all Patching Universes"""
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

import proto
from model.patching_universe import PatchingUniverse
from view.patching.patch_plan_widget import PatchPlanWidget

if TYPE_CHECKING:
    from view.main_window import MainWindow


class PatchingSelector(QtWidgets.QTabWidget):
    """selector for Patching witch holds all Patching Universes"""

    def __init__(self, parent: "MainWindow"):
        super().__init__(parent=parent)
        self._parent: "MainWindow" = parent
        self._patching_universes: list[PatchingUniverse] = []
        self._patch_planes: list[PatchPlanWidget] = []
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
        self.addTab(QtWidgets.QWidget(), "+")
        # self.currentChanged.connect(self._tab_changed)
        self.tabBarClicked.connect(self._tab_clicked)
        self._add_universe()
        self.tabBar().setCurrentIndex(0)

    def _add_universe(self) -> None:
        """add a new Universe to universe Selector"""
        universe = PatchingUniverse(proto.UniverseControl_pb2.Universe(
            id=len(self._patching_universes) + 1,
            remote_location=proto.UniverseControl_pb2.Universe.ArtNet(
                ip_address="10.0.15.1",
                port=6454,
                universe_on_device=len(self._patching_universes) + 1
            )
            # ftdi_dongle=proto.UniverseControl_pb2.Universe.USBConfig(
            #    vendor_id=0x0403,
            #    product_id=0x6001,
            #    serial="",
            #    device_name=""
            # )
        ), None)
        self._patching_universes.append(universe)
        if self._parent.fish_connector.is_running:
            self._parent.fish_connector.generate_universe(universe)
        #    self._parent.fish_connector.send_universe(universe) TODO woanders hin
        patch_plan = PatchPlanWidget(universe, parent=self)
        self._patch_planes.append(patch_plan)
        self.insertTab(self.tabBar().count() - 1, patch_plan, str(universe.universe_proto.id))

    def _tab_clicked(self, scene_index: int) -> None:
        self._last_tab = self.tabBar().currentIndex()
        if scene_index == self.tabBar().count() - 1:
            self._add_universe()
