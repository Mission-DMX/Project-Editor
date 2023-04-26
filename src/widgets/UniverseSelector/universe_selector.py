# coding=utf-8
"""select Universe"""
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

import proto.UniverseControl_pb2
from DMXModel import Universe
from Network import NetworkManager
from Style import Style
from widgets.DirectEditor.DirectEditorWidget import DirectEditorWidget
from widgets.PatchPlan.patch_plan_widget import PatchPlanWidget


class UniverseSelector(QtWidgets.QTabWidget):
    """select Universe from Tab Widget"""

    def __init__(self, fish_connector: NetworkManager, universes: list[Universe] = None, parent=None) -> None:
        super().__init__(parent=parent)
        if universes is None:
            universes = []
        self._universes: list[Universe] = universes
        self._fish_connector = fish_connector
        self.setStyleSheet(Style.WIDGET)
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
        for universe in self._universes:
            self.add_universe(universe)
        if len(universes) == 0:
            self.add_universe(None)

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
            ))
        if universe not in self._universes:
            self._universes.append(universe)

        if self._fish_connector.is_running:
            self._fish_connector.generate_universe(universe)
            self._fish_connector.send_universe(universe)

        splitter = QtWidgets.QSplitter(self)
        splitter.setOrientation(Qt.Vertical)

        custom_editor: PatchPlanWidget = PatchPlanWidget(universe, parent=splitter)
        splitter.addWidget(custom_editor)

        direct_editor: DirectEditorWidget = DirectEditorWidget(universe, self._fish_connector, parent=splitter)
        splitter.addWidget(direct_editor)

        self.addTab(splitter, str(universe.universe_proto.id))

    def universe_coppy(self) -> list[Universe]:
        """coppy a whole universe by creating a new one"""
        universes_copy: list[Universe] = []
        for universe in self._universes:
            universe_copy = Universe(universe.universe_proto)
            universes_copy.append(universe_copy)
        return universes_copy
