# coding=utf-8
"""select Universe"""

from PySide6 import QtWidgets, QtCore

from model.patching_universe import PatchingUniverse
from model.universe import Universe
from view.direct_mode.direct_universe_widget import DirectUniverseWidget


class UniverseSelector(QtWidgets.QTabWidget):
    """select Universe from Tab Widget"""
    send_universe_value: QtCore.Signal = QtCore.Signal(Universe)

    def __init__(self, parent, patching_universes: list[PatchingUniverse] = None) -> None:
        super().__init__(parent=parent)
        self._universes: list[Universe] = []
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        if patching_universes is not None:
            for patching_universe in patching_universes:
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
        self.send_universe_value.emit(universe)
        self._universes.append(universe)

        direct_editor: DirectUniverseWidget = DirectUniverseWidget(universe, parent=self)
        direct_editor.send_universe_value.connect(self.send_universe_value.emit)

        self.addTab(direct_editor, str(universe.universe_proto.id))

    def send_all_universe(self) -> None:
        """send all universes to fish"""
        for universe in self._universes:
            self.send_universe_value.emit(universe)
