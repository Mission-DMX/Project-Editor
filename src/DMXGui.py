"""GUI and control elements for the software."""

import logging
import sys
from typing import Callable

from PySide6 import QtWidgets, QtGui

from DMXModel import Universe
from Network import NetworkManager
from src.Style import Style
from widgets.universe_selector import UniverseSelector


class MainWindow(QtWidgets.QMainWindow):
    """Main window of the app. All widget are children of its central widget."""

    def __init__(self, parent=None):
        """Inits the MainWindow.

        Args:
            parent: Qt parent of the widget.
        """
        super().__init__(parent)

        self.setWindowTitle("Project-Editor")

        # DMX data. Each universe contains 512 channels
        self._universes: list[Universe] = [Universe(1)]

        self._fisch_connector: NetworkManager = NetworkManager()
        self._universe_selector = UniverseSelector(self._universes, self._fisch_connector, self)

        self.setCentralWidget(self._universe_selector)

        self._setup_menubar()
        self._setup_toolbar()

    def _setup_menubar(self) -> None:
        """Adds a menubar with submenus."""
        self.setMenuBar(QtWidgets.QMenuBar())
        menus: dict[str, list[list[str, Callable]]] = {"File": [["save", self._save_scene]],
                                                       "Universe": [["add", self._add_universe],
                                                                    ["remove", self._remove_universe]],
                                                       "Fish": [["Connect", self._start_connection],
                                                                ["Disconnect", self._fisch_connector.disconnect]]}
        for name, entries in menus.items():
            menu: QtWidgets.QMenu = QtWidgets.QMenu(name, self.menuBar())
            self._add_entries_to_menu(menu, entries)
            self.menuBar().addAction(menu.menuAction())

    def _add_entries_to_menu(self, menu, entries: list[list[str, Callable]]) -> None:
        for entry in entries:
            menu_entry: QtGui.QAction = QtGui.QAction(entry[0], self)
            menu_entry.triggered.connect(entry[1])
            menu.addAction(menu_entry)

    def _add_universe(self) -> None:
        self._universes.append(Universe(len(self._universes) + 1))
        self._universe_selector.add_universe(self._universes[len(self._universes) - 1])
        self._fisch_connector.generate_universe(self._universes[len(self._universes) - 1])

    def _remove_universe(self) -> None:
        """TODO"""
        pass

    def _start_connection(self):
        self._fisch_connector.start()
        for universe in self._universes:
            self._fisch_connector.generate_universe(universe)

    def _setup_toolbar(self) -> None:
        """Adds a toolbar with actions."""
        toolbar = self.addToolBar("Mode")
        self.__switch_mode_action = QtGui.QAction(self)
        self.__switch_mode_action.setText("Direct Mode")
        self.__switch_mode_action.triggered.connect(self._switch_mode)
        toolbar.addAction(self.__switch_mode_action)

    def _switch_mode(self) -> None:
        """Switches between direct and filter mode."""
        current_mode = self.__switch_mode_action.text()
        if current_mode == "Direct Mode":
            self.__switch_mode_action.setText("Filter Mode")
        else:
            self.__switch_mode_action.setText("Direct Mode")

    def _save_scene(self) -> None:
        """Safes the current scene to a file.
        TODO implement saving to xml file with xsd schema. See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd
        """
        pass


if __name__ == "__main__":
    logging.basicConfig(encoding='utf-8', level=logging.ERROR)
    logging.info("start DMXGui")
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    screen_width = app.primaryScreen().size().width()
    screen_height = app.primaryScreen().size().height()
    widget = MainWindow()
    widget.showMaximized()

    sys.exit(app.exec())
