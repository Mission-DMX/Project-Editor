# coding=utf-8
"""GUI and control elements for the software."""

import logging
import sys
from typing import Callable

import pyqtgraph
from PySide6 import QtWidgets, QtGui

from Network import NetworkManager
from src.Style import Style
from widgets.SzeneEditor.szene_editor import SzeneEditor


class MainWindow(QtWidgets.QMainWindow):
    """Main window of the app. All widget are children of its central widget."""

    def __init__(self, parent=None) -> None:
        """Inits the MainWindow.

        Args:
            parent: Qt parent of the widget.
        """
        super().__init__(parent)

        self.setWindowTitle("Project-Editor")

        # DMX data. Each universe contains 512 channels
        self._universes: list[Universe] = [Universe(1)]

        self._fish_connector: NetworkManager = NetworkManager()
        self._fish_connector.start()
        self._szene_editor = SzeneEditor(self._fish_connector, self)

        self.setCentralWidget(self._szene_editor)

        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()

    def _setup_menubar(self) -> None:
        """Adds a menubar with submenus."""
        self.setMenuBar(QtWidgets.QMenuBar())
        menus: dict[str, list[list[str, Callable]]] = {"File": [["save", self._save_scenes],
                                                                ["load", self._load_scenes]],
                                                       "Szene": [["add", self._add_szene]],
                                                       "Universe": [["add", self._szene_editor.add_universe],
                                                                    ["remove", self._remove_universe]],
                                                       "Fish": [["Connect", self._start_connection],
                                                                ["Disconnect", self._fish_connector.disconnect],
                                                                ["Change", self._change_server_name]]}
        for name, entries in menus.items():
            menu: QtWidgets.QMenu = QtWidgets.QMenu(name, self.menuBar())
            self._add_entries_to_menu(menu, entries)
            self.menuBar().addAction(menu.menuAction())

    def _add_entries_to_menu(self, menu: QtWidgets.QMenu, entries: list[list[str, Callable]]) -> None:
        """ add entries to a menu"""
        for entry in entries:
            menu_entry: QtGui.QAction = QtGui.QAction(entry[0], self)
            menu_entry.triggered.connect(entry[1])
            menu.addAction(menu_entry)

    def _add_szene(self) -> None:
        """add a new szene"""
        self._szene_editor.add_szene("Baum")

    def _remove_universe(self) -> None:
        """TODO"""
        pass

    def _start_connection(self) -> None:
        """start connection with fish server"""
        self._fish_connector.start()
        self._szene_editor.start()

    def _change_server_name(self) -> None:
        """change fish socket name"""
        self._fish_connector.change_server_name(self._get_server_name())

    def _save_scenes(self) -> None:
        """Safes the current scene to a file.
        TODO implement saving to xml file with xsd schema.
         See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd
        """
        data: str = ""
        for szene in self._szene_editor.scenes:
            for universe in szene.universes:
                data += ""
                for channel in universe.channels:
                    data += str(channel.value) + ","
                data = data[:-1]
                data += ";"
            data = data[:-1]
            data += "\n"

        with open("szenes.txt", "w") as f:
            f.write(data)

    def _load_scenes(self):
        pass
        with open("szenes.txt", "r") as f:
            for line in f:
                universes = line.split(";")
                universe_id = 0
                for universe in universes:
                    universe_id += 1
                    chanel = 0
                    for value in universe.split(","):
                        chanel += 1
                        self._szene_editor.scenes[0].universes[universe_id].channels[chanel].value = int(value)

    def _get_server_name(self) -> str:
        """select a new socket name over an input dialog"""
        text, ok = QtWidgets.QInputDialog.getText(self, 'Server Name', 'Enter Server Name:')
        if ok:
            return str(text)

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

    def _setup_statusbar(self) -> None:
        """ build statusbor"""
        status_bar = QtWidgets.QStatusBar()
        status_bar.setMaximumHeight(50)
        self.setStatusBar(status_bar)

        label_state_update = QtWidgets.QLabel(self._fish_connector.connection_state(), status_bar)
        self._fish_connector.connection_state_updated.connect(lambda txt: label_state_update.setText(txt))
        status_bar.addWidget(label_state_update)

        label_last_error = QtWidgets.QLabel("Error", status_bar)
        self._fish_connector.status_updated.connect(lambda txt: label_last_error.setText(txt))
        status_bar.addWidget(label_last_error)

        last_cycle_time_widget = pyqtgraph.plot()
        last_cycle_time_widget.getPlotItem().hideAxis('bottom')
        # last_cycle_time_widget.getPlotItem().hideAxis('left')

        items = 1000
        self.time = list(range(items))
        self._last_cycle_time = [0] * items

        self._last_cycle_time_plot = last_cycle_time_widget.plot(self.time, self._last_cycle_time)
        last_cycle_time_widget.setXRange(0, items, padding=0)
        last_cycle_time_widget.setYRange(0, 40000, padding=0)
        self._fish_connector.last_cycle_time_update.connect(lambda cycle: self._update_last_cycle_time(cycle))
        status_bar.addWidget(last_cycle_time_widget)

    def _update_last_cycle_time(self, new_value: int):
        """update plot of fish last cycle Time"""
        self._last_cycle_time = self._last_cycle_time[1:]  # Remove the first y element.
        self._last_cycle_time.append(new_value)  # Add a new value

        self._last_cycle_time_plot.setData(self.time, self._last_cycle_time)


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
