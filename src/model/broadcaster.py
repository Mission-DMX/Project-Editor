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

    switch_view_to_patch: QtCore.Signal = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.add_universe.connect(self._add_universe)
        self.connection_state_updated.connect(self._connection_changed)

    def _add_universe(self, universe: PatchingUniverse):
        self.patching_universes.append(universe)
        self.send_universe.emit(universe)

    def _connection_changed(self, connected):
        """connection to fish is changed"""
        if connected:
            for universe in self.patching_universes:
                self.send_universe.emit(universe)
