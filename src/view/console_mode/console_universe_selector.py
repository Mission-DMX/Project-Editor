# coding=utf-8
"""select Universe"""

from PySide6 import QtWidgets

from model.broadcaster import Broadcaster
from model.patching_universe import PatchingUniverse
from model.universe import Universe
from view.console_mode.console_universe_widget import DirectUniverseWidget


class UniverseSelector(QtWidgets.QTabWidget):
    """select Universe from Tab Widget"""

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self._broadcaster = Broadcaster()
        self._universes: list[Universe] = []
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        if self._broadcaster.patching_universes:
            for patching_universe in self._broadcaster.patching_universes:
                self.add_universe(patching_universe)

    @property
    def universes(self) -> list[Universe]:
        """Universes"""
        return self._universes

    def add_universe(self, patching_universe: PatchingUniverse) -> None:
        """
        add a new Universe to universe Selector
        Args:
            patching_universe: the new universe to add
        """
        universe = Universe(patching_universe)
        self._broadcaster.send_universe_value.emit(universe)
        self._universes.append(universe)

        direct_editor: DirectUniverseWidget = DirectUniverseWidget(universe, parent=self)

        self.addTab(direct_editor, str(universe.universe_proto.id))

    def send_all_universe(self) -> None:
        """send all universes to fish"""
        for universe in self._universes:
            self._broadcaster.send_universe_value.emit(universe)
