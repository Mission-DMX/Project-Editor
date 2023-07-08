# coding=utf-8
"""mange different scenes"""
import logging
from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets

from model.broadcaster import Broadcaster
from model.patching_universe import PatchingUniverse
from view.console_mode.console_universe_selector import UniverseSelector

if TYPE_CHECKING:
    from view.main_window import MainWindow


class ConsoleSceneSelector(QtWidgets.QTabWidget):
    """Widget to mange different scenes in Tab Widgets"""

    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent=parent)
        broadcaster = Broadcaster()
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self._last_tab: int = 0
        self._scenes: list[UniverseSelector] = []
        self.addTab(QtWidgets.QWidget(), "+")
        self.currentChanged.connect(self._tab_changed)
        self.tabBarClicked.connect(self._tab_clicked)
        broadcaster.add_universe.connect(self.add_universe)

        self._toolbar: list[QtGui.QAction] = []
        save_button = QtGui.QAction("Save")
        load_button = QtGui.QAction("Load")
        save_button.triggered.connect(self._save_scenes)
        load_button.triggered.connect(self._load_scenes)
        self._toolbar.append(save_button)
        self._toolbar.append(load_button)

    @property
    def toolbar(self) -> list[QtGui.QAction]:
        """toolbar for Console mode"""
        return self._toolbar

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

    def _add_scene(self, text: str = None) -> None:
        """
        add a new scene
        """
        if not text:
            text, run = QtWidgets.QInputDialog.getText(self, "Scene Name", "Enter Scene Name:")
        else:
            run = True
        if run:
            universe_selector = UniverseSelector(self)
            self._scenes.append(universe_selector)
            self.insertTab(self.tabBar().count() - 1, self._scenes[-1], text)

    def _rename_scene(self, index: int) -> None:
        text, run = QtWidgets.QInputDialog.getText(self, f"Rename {self.tabText(index)} ", "Enter new Scene Name:")
        if run:
            self.setTabText(index, text)

    def _remove_scene(self, index: int) -> None:
        self.removeTab(index)
        self._scenes.remove(self._scenes[index])
        if index == len(self._scenes) and index != 0:
            self.tabBar().setCurrentIndex(index - 1)

    def add_universe(self, universe: PatchingUniverse) -> None:
        """ add a new universe """
        for scene in self._scenes:
            scene.add_universe(universe)

    def _tab_changed(self, scene_index: int) -> None:
        """
        send all universes if tab changed
        Args:
            scene_index: index of current scene
        """
        if scene_index == self.tabBar().count() - 1:
            self.tabBar().setCurrentIndex(self._last_tab)
        else:
            self._scenes[scene_index].send_all_universe()
            self._scenes[scene_index].notify_activate()

    def _tab_clicked(self, scene_index: int) -> None:
        self._last_tab = self.tabBar().currentIndex()
        if scene_index == self.tabBar().count() - 1:
            self._add_scene()

    def _save_scenes(self) -> None:
        """Safes the current scene to a file.
        TODO implement saving to xml file with xsd schema.
         See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd
        """
        data: str = ""
        for index, scene in enumerate(self._scenes):
            for universe in scene.universes:
                data += ""
                for channel in universe.channels:
                    data += str(channel.value) + ","
                data = data[:-1]
                data += ";"
            data = data[:-1]
            data += f"# {self.tabText(index)}\n"
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "save Scene", "",
                                                             "Text Files (*.txt);;All Files (*)", )
        if file_name:
            with open(file_name, "w", encoding='UTF-8') as file:
                file.write(data)

    def _load_scenes(self) -> None:
        """load scene from file"""
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "load Scene", "",
                                                             "Text Files (*.txt);;All Files (*)", )
        if file_name:
            with open(file_name, "r", encoding='UTF-8') as file:
                for (scene_index, line) in enumerate(file):
                    name = line.split("\n")[0]
                    name = name.split("#")[1]
                    line = line.split("#")[0]
                    logging.info(f"Add scene {name}")
                    if scene_index == len(self._scenes):
                        self._add_scene(name)

                    universes = line.split(";")
                    for (universe_index, universe) in enumerate(universes):
                        for (chanel, value) in enumerate(universe.split(",")):
                            self._scenes[scene_index].universes[universe_index].channels[chanel].value = int(value)
