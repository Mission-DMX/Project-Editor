# coding=utf-8
"""mange different scenes"""
from PySide6 import QtWidgets, QtGui

from Network import NetworkManager
from Style import Style
from ofl.fixture import UsedFixture
from widgets.UniverseSelector.universe_selector import UniverseSelector


class SceneEditor(QtWidgets.QTabWidget):
    """Widget to mange different scenes in Tab Widgets"""

    def __init__(self, fish_connector: NetworkManager, parent=None) -> None:
        super().__init__(parent=parent)
        self._fish_connector = fish_connector
        self.setStyleSheet(Style.WIDGET)
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self._scenes: list[UniverseSelector] = [UniverseSelector(self._fish_connector, None, self)]
        self.addTab(self._scenes[0], "start")
        self.currentChanged.connect(self.tab_changed)

    @property
    def scenes(self) -> list[UniverseSelector]:
        """current Scenes"""
        return self._scenes

    def contextMenuEvent(self, event):
        """context menu"""
        for index in range(self.tabBar().count()):
            if self.tabBar().tabRect(index).contains(event.pos()):
                menu = QtWidgets.QMenu(self)
                add_scene = QtGui.QAction('add Scene', self)
                rename_scene = QtGui.QAction('rename Scene', self)
                delete_scene = QtGui.QAction('delete Scene', self)
                add_scene.triggered.connect(lambda: self.add_scene())
                rename_scene.triggered.connect(
                    lambda: self._rename_scene(index))
                delete_scene.triggered.connect(lambda: self._remove_scene(index))
                menu.addAction(add_scene)
                menu.addAction(rename_scene)
                menu.addAction(delete_scene)
                menu.popup(QtGui.QCursor.pos())
                break

    def add_scene(self) -> None:
        """
        add a new scene
        """
        text, ok = QtWidgets.QInputDialog.getText(self, "Scene Name", "Enter Scene Name:")
        if ok:
            self._scenes.append(
                UniverseSelector(self._fish_connector, self._scenes[0].universe_coppy(), self))
            self.addTab(self._scenes[-1], text)

    def _rename_scene(self, index: int) -> None:
        text, ok = QtWidgets.QInputDialog.getText(self, f"Rename {self.tabText(index)} ", "Enter new Scene Name:")
        if ok:
            self.setTabText(index, text)

    def _remove_scene(self, index: int) -> None:
        self.removeTab(index)
        self._scenes.remove(self._scenes[index])

    def add_universe(self) -> None:
        """ add a new universe """
        for scene in self._scenes:
            scene.add_universe()

    def start(self) -> None:
        """start connection to fish"""
        for scene in self._scenes:
            scene.start()

    def tab_changed(self, scene_index: int) -> None:
        """
        send all universes if tab changed
        Args:
            scene_index: index of current scene
        """
        self._scenes[scene_index].send_all_universe()

    def patch(self, fixture: UsedFixture, patching: str) -> None:
        """
        patch a fixture to all scenes
        Args:
            fixture: fixture to patch
            patching: patching string
        """

        universe, updated = self._scenes[0].patch(fixture, patching)
        for scene in self._scenes:
            scene.patch_update(universe, updated)
