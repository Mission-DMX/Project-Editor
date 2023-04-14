# coding=utf-8
"""mange different scenes"""
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from DMXModel import Universe
from Network import NetworkManager
from Style import Style
from widgets.UniverseSelector.universe_selector import UniverseSelector


class SzeneEditor(QtWidgets.QTabWidget):
    """Widget to mange different scenes in Tab Widgets"""

    def __init__(self, universes: list[Universe], fish_connector: NetworkManager, parent=None) -> None:
        super().__init__(parent=parent)
        self._universes = universes
        self._fish_connector = fish_connector
        self.setStyleSheet(Style.WIDGET)
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.scenes: list[UniverseSelector] = []
        self.add_szene()

    def add_szene(self) -> None:
        universes_copy = []
        for universe in self._universes:
            universe_copy = Universe(universe.address)
            universes_copy.append(universe_copy)

        self.scenes.append(UniverseSelector(universes_copy, self._fish_connector, self))
        self.addTab(self.scenes[-1], "Baum")

    def add_universe(self, universe: Universe) -> None:
        self.scenes[0].add_universe(universe)
        self._universes.append(universe)
        for scene in self.scenes[1:]:
            universe_copy = Universe(universe.address)
            scene.add_universe(universe_copy)



