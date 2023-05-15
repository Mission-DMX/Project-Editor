# coding=utf-8
"""mange different scenes"""
from PySide6 import QtWidgets, QtGui

from Network import NetworkManager
from Style import Style
from ofl.fixture import UsedFixture
from view.direct_mode.SceneEditor.UniverseSelector.universe_selector import UniverseSelector


class SceneEditor(QtWidgets.QTabWidget):
    """Widget to mange different scenes in Tab Widgets"""

    def __init__(self, fish_connector: NetworkManager, parent=None) -> None:
        super().__init__(parent=parent)
        self._fish_connector = fish_connector
        self.setStyleSheet(Style.WIDGET)
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self._scenes: list[UniverseSelector] = []
        self.addTab(QtWidgets.QWidget(), "+")
        self.currentChanged.connect(self._tab_changed)
        self.tabBarClicked.connect(self._tab_clicked)

    @property
    def scenes(self) -> list[UniverseSelector]:
        """current Scenes"""
        return self._scenes

    def contextMenuEvent(self, event):
        """context menu"""
        for index in range(self.tabBar().count() - 1):
            if self.tabBar().tabRect(index).contains(event.pos()):
                menu = QtWidgets.QMenu(self)

                rename_scene = QtGui.QAction('rename Scene', self)
                delete_scene = QtGui.QAction('delete Scene', self)
                rename_scene.triggered.connect(lambda: self._rename_scene(index))
                delete_scene.triggered.connect(lambda: self._remove_scene(index))
                menu.addAction(rename_scene)
                menu.addAction(delete_scene)
                menu.popup(QtGui.QCursor.pos())
                break

    def _add_scene(self) -> None:
        """
        add a new scene
        """
        text, ok = QtWidgets.QInputDialog.getText(self, "Scene Name", "Enter Scene Name:")
        if ok:
            if self._scenes:
                self._scenes.append(
                    UniverseSelector(self._fish_connector, self._scenes[0].universe_coppy(), self))
            else:
                self._scenes.append(UniverseSelector(self._fish_connector, None, self))
            self.insertTab(self.tabBar().count() - 1, self._scenes[-1], text)

    def _rename_scene(self, index: int) -> None:
        text, ok = QtWidgets.QInputDialog.getText(self, f"Rename {self.tabText(index)} ", "Enter new Scene Name:")
        if ok:
            self.setTabText(index, text)

    def _remove_scene(self, index: int) -> None:
        self.removeTab(index)
        self._scenes.remove(self._scenes[index])
        if index == len(self._scenes) and index != 0:
            self.tabBar().setCurrentIndex(index - 1)

    def add_universe(self) -> None:
        """ add a new universe """
        for scene in self._scenes:
            scene.add_universe()

    def start(self) -> None:
        """start connection to fish"""
        for scene in self._scenes:
            scene.start()

    def _tab_changed(self, scene_index: int) -> None:
        """
        send all universes if tab changed
        Args:
            scene_index: index of current scene
        """
        print(scene_index)
        if scene_index == self.tabBar().count() - 1:
            self.tabBar().setCurrentIndex(self._last_tab)
        else:
            self._scenes[scene_index].send_all_universe()

    def _tab_clicked(self, scene_index: int) -> None:
        self._last_tab = self.tabBar().currentIndex()
        if scene_index == self.tabBar().count() - 1:
            self._add_scene()

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
