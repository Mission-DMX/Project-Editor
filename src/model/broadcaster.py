# coding=utf-8
"""connector for Signals"""

from PySide6 import QtCore

from model.patching_universe import PatchingUniverse
from model.universe import Universe


class Broadcaster(QtCore.QObject):
    """connector for Signals"""
    connection_state_updated: QtCore.Signal = QtCore.Signal(bool)
    add_universe: QtCore.Signal = QtCore.Signal(PatchingUniverse)
    send_universe: QtCore.Signal = QtCore.Signal(PatchingUniverse)
    send_universe_value: QtCore.Signal = QtCore.Signal(Universe)
    patching_universes: list[PatchingUniverse] = []

    def __init__(self):
        super().__init__()
        self.add_universe.connect(self._add_universe)

    def _add_universe(self, universe: PatchingUniverse):
        self.patching_universes.append(universe)
