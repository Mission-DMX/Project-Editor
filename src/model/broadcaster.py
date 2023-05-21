# coding=utf-8
"""connector for Signals"""
import random
import re

from PySide6 import QtCore

from model.patching_universe import PatchingUniverse
from model.universe import Universe
from view.dialogs.patching_dialog import PatchingDialog


class Broadcaster(QtCore.QObject):
    """connector for Signals"""
    connection_state_updated: QtCore.Signal = QtCore.Signal(bool)
    add_universe: QtCore.Signal = QtCore.Signal(PatchingUniverse)
    send_universe: QtCore.Signal = QtCore.Signal(PatchingUniverse)
    send_universe_value: QtCore.Signal = QtCore.Signal(Universe)
    patching_universes: list[PatchingUniverse] = []

    view_to_patch_menu: QtCore.Signal = QtCore.Signal()
    view_patch: QtCore.Signal = QtCore.Signal()

    view_is_patch_menu: QtCore.Signal = QtCore.Signal()
    view_is_not_patch_menu: QtCore.Signal = QtCore.Signal()
    view_is_patching: QtCore.Signal = QtCore.Signal()

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

    def patch(self) -> None:
        """
        patch a specific fixture

        Returns:
            universe: the index of modified universe
            updated: list of indices of modified channels

        """
        self.view_is_patching.emit()
        form = PatchingDialog()
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
                    item = self.patching_universes[universe].patching[channel + index]
                    item.fixture = fixture
                    item.fixture_channel = index
                    item.color = color
                if offset == 0:
                    channel += len(fixture.mode['channels'])
                else:
                    channel += offset
        self.view_is_patch_menu.emit()
