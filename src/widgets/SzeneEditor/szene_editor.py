# coding=utf-8
"""mange different scenes"""
from PySide6 import QtWidgets

from Network import NetworkManager
from Style import Style
from widgets.UniverseSelector.universe_selector import UniverseSelector


class SzeneEditor(QtWidgets.QTabWidget):
    """Widget to mange different scenes in Tab Widgets"""

    def __init__(self, fish_connector: NetworkManager, parent=None) -> None:
        super().__init__(parent=parent)
        self._fish_connector = fish_connector
        self.setStyleSheet(Style.WIDGET)
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self._scenes: list[UniverseSelector] = [UniverseSelector(self._fish_connector, None, self)]
        self.addTab(self._scenes[0], "start")

    @property
    def scenes(self) -> list[UniverseSelector]:
        """Scene property"""
        return self._scenes

    def add_szene(self, name) -> None:
        self._scenes.append(UniverseSelector(self._fish_connector, self._scenes[0].universe_coppy(), self))
        self.addTab(self._scenes[-1], name)

    def add_universe(self) -> None:
        for scene in self._scenes:
            scene.add_universe()

    def start(self):
        for universe in self._universes:
            if self._fish_connector.is_running:
                self._fish_connector.generate_universe(universe)
