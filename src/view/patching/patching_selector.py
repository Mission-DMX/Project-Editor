# coding=utf-8
"""selector for Patching witch holds all Patching Universes"""
import random
import re
from typing import TYPE_CHECKING

from PySide6 import QtWidgets, QtGui, QtCore

import proto
from model.patching_universe import PatchingUniverse
from ofl.patching_dialog import PatchingDialog
from view.patching.patch_plan_widget import PatchPlanWidget

if TYPE_CHECKING:
    from view.main_window import MainWindow


class PatchingSelector(QtWidgets.QTabWidget):
    """selector for Patching witch holds all Patching Universes"""
    send_universe: QtCore.Signal = QtCore.Signal(PatchingUniverse)

    def __init__(self, parent: "MainWindow"):
        super().__init__(parent=parent)
        parent.connection_state_updated.connect(self._connection_changed)
        self._patching_universes: list[PatchingUniverse] = parent.patching_universes
        self._patch_planes: list[PatchPlanWidget] = []
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.addTab(QtWidgets.QWidget(), "+")
        # self.currentChanged.connect(self._tab_changed)
        self.tabBarClicked.connect(self._tab_clicked)
        self.tabBar().setCurrentIndex(0)

        self._toolbar: list[QtGui.QAction] = []
        patch_button = QtGui.QAction("Patch")
        patch_button.triggered.connect(self.patch)
        self._toolbar.append(patch_button)

    @property
    def toolbar(self) -> list[QtGui.QAction]:
        """toolbar for patching"""
        return self._toolbar

    def _add_universe(self) -> None:
        """add a new Universe to universe Selector"""
        # TODO add universe Dialog
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
        self.send_universe.emit(universe)

        patch_plan = PatchPlanWidget(universe, parent=self)
        self._patch_planes.append(patch_plan)
        self.insertTab(self.tabBar().count() - 1, patch_plan, str(universe.universe_proto.id))

    def _connection_changed(self, connected):
        """connection to fish is changed"""
        if connected:
            for universe in self._patching_universes:
                self.send_universe.emit(universe)
                #    self._parent.fish_connector.send_universe(universe) TODO woanders hin

    def _tab_clicked(self, scene_index: int) -> None:
        if scene_index == self.tabBar().count() - 1:
            self._add_universe()

    def patch(self) -> None:
        """
        patch a specific fixture

        Returns:
            universe: the index of modified universe
            updated: list of indices of modified channels

        """
        form = PatchingDialog(self)
        if form.exec():
            fixture = form.get_used_fixture()
            patching = form.patching.text()
            if patching[0] == "@":
                patching = "1" + patching
            spliter = re.split('@|-|/', patching)
            spliter += [0] * (4 - len(spliter))
            spliter = list(map(int, spliter))
            number = spliter[0]
            universe = spliter[1] - 1
            channel = spliter[2] - 1
            offset = spliter[3]

            if channel == -1:
                channel = 0
            for _ in range(number):
                color = "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
                for index in range(len(fixture.mode['channels'])):
                    item = self._patching_universes[universe].patching[channel + index]
                    item.fixture = fixture
                    item.fixture_channel = index
                    item.color = color
                if offset == 0:
                    channel += len(fixture.mode['channels'])
                else:
                    channel += offset
