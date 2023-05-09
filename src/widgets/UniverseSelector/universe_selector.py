# coding=utf-8
"""select Universe"""
import random
import re

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

import proto.UniverseControl_pb2
from DMXModel import Universe
from Network import NetworkManager
from Style import Style
from ofl.fixture import UsedFixture
from widgets.DirectEditor.DirectEditorWidget import DirectEditorWidget
from widgets.PatchPlan.patch_plan_widget import PatchPlanWidget


class UniverseSelector(QtWidgets.QTabWidget):
    """select Universe from Tab Widget"""

    def __init__(self, fish_connector: NetworkManager, universes: list[Universe] = None, parent=None) -> None:
        super().__init__(parent=parent)
        if universes is None:
            universes = []
        self._universes: list[Universe] = universes
        self._patch_planes: list[PatchPlanWidget] = []
        self._fish_connector = fish_connector
        self.setStyleSheet(Style.WIDGET)
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        if len(universes) == 0:
            self.add_universe(None)
        else:
            for universe in self._universes:
                self.add_universe(universe)

    @property
    def universes(self) -> list[Universe]:
        """Universes property"""
        return self._universes

    def add_universe(self, universe: Universe = None) -> None:
        """
        add a new Universe to universe Selector
        Args:
            universe: the new universe to select
        """
        if universe is None:
            universe = Universe(proto.UniverseControl_pb2.Universe(
                id=len(self._universes) + 1,
                remote_location=proto.UniverseControl_pb2.Universe.ArtNet(
                    ip_address="10.0.15.1",
                    port=6454,
                    universe_on_device=len(self._universes) + 1
                )
                # ftdi_dongle=proto.UniverseControl_pb2.Universe.USBConfig(
                #    vendor_id=0x0403,
                #    product_id=0x6001,
                #    serial="",
                #    device_name=""
                # )
            ), None)
        if universe not in self._universes:
            self._universes.append(universe)

        if self._fish_connector.is_running:
            self._fish_connector.generate_universe(universe)
            self._fish_connector.send_universe(universe)

        splitter = QtWidgets.QSplitter(self)
        splitter.setOrientation(Qt.Vertical)

        patch_plan = PatchPlanWidget(universe, parent=splitter)
        splitter.addWidget(patch_plan)
        self._patch_planes.append(patch_plan)

        direct_editor: DirectEditorWidget = DirectEditorWidget(universe, self._fish_connector, parent=splitter)
        splitter.addWidget(direct_editor)

        self.addTab(splitter, str(universe.universe_proto.id))

    def universe_coppy(self) -> list[Universe]:
        """coppy a whole universe by creating a new one"""
        universes_copy: list[Universe] = []
        for universe in self._universes:
            universe_copy = Universe(universe.universe_proto, universe.patching)
            universes_copy.append(universe_copy)
        return universes_copy

    def start(self) -> None:
        """start connection with fish"""
        for universe in self._universes:
            if self._fish_connector.is_running:
                self._fish_connector.generate_universe(universe)

    def send_all_universe(self) -> None:
        """send all universes to fish"""
        for universe in self._universes:
            self._fish_connector.send_universe(universe)

    def patch(self, fixture: UsedFixture, patching: str) -> tuple[int, list[int]]:
        """
        patch a specific fixture
        Args:
            fixture: fixture to patch
            patching: patching String

        Returns:
            universe: the index of modified universe
            updated: list of indices of modified channels

        """
        if patching[0] == "@":
            patching = "1" + patching
        spliter = re.split('@|-|/', patching)
        spliter += [0] * (4 - len(spliter))
        spliter = list(map(int, spliter))
        number = spliter[0]
        universe = spliter[1] - 1
        channel = spliter[2] - 1
        offset = spliter[3]

        updated: list[int] = []
        for _ in range(number):
            color = "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
            for index in range(len(fixture.mode['channels'])):
                modified: int = channel + index
                updated.append(modified)
                item = self._universes[universe].patching[modified]
                item.fixture = fixture
                item.fixture_channel = index
                item.color = color
            if offset == 0:
                channel += len(fixture.mode['channels'])
            else:
                channel += offset
        return universe, updated

    def patch_update(self, universe: int, modified: list[int]) -> None:
        """
        update patch items
        Args:
            universe: universe to update
            modified: list of indices of modified channels
        """
        for index in modified:
            self._patch_planes[universe].update_patching(index)
