# coding=utf-8
"""GUI and control elements for the software."""

import logging
import sys
from typing import Callable

import xml.etree.ElementTree as ET

from PySide6 import QtWidgets, QtGui

from DMXModel import BoardConfiguration
from Network import NetworkManager
from ShowFile import createXML, writeDocument
from ofl.patching_dialog import PatchingDialog
from src.Style import Style
from widgets.Logging.logging_widget import LoggingWidget
from widgets.NodeEditor.NodeEditor import NodeEditorWidget
from widgets.SzeneEditor.szene_editor import SzeneEditor


class MainWindow(QtWidgets.QMainWindow):
    """Main window of the app. All widget are children of its central widget."""

    def __init__(self, parent=None) -> None:
        """Inits the MainWindow.

        Args:
            parent: Qt parent of the widget.
        """
        super().__init__(parent)
        # first logging to don't miss logs
        self._debug_console = LoggingWidget()

        self.setWindowTitle("Project-Editor")

        self._widgets = QtWidgets.QStackedWidget()

        self._board_configuration: BoardConfiguration = BoardConfiguration()

        self._fish_connector: NetworkManager = NetworkManager()
        self._fish_connector.start()
        self._szene_editor = SzeneEditor(self._fish_connector, self)

        self._node_editor = NodeEditorWidget(self, self._board_configuration)
        self._node_editor.move(200, 200)

        self._widgets.addWidget(self._szene_editor)
        self._widgets.addWidget(self._node_editor)
        self._widgets.addWidget(self._debug_console)

        self.setCentralWidget(self._widgets)

        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()

    def _setup_menubar(self) -> None:
        """Adds a menubar with submenus."""
        self.setMenuBar(QtWidgets.QMenuBar())
        menus: dict[str, list[list[str, Callable]]] = {"File": [["save", self._save_scenes],
                                                                ["load", self._load_scenes],
                                                                ["Config", self._edit_config]],
                                                       "Szene": [["add", self._add_szene]],
                                                       "Universe": [["add", self._szene_editor.add_universe],
                                                                    ["remove", self._remove_universe]],
                                                       "Fish": [["Connect", self._start_connection],
                                                                ["Disconnect", self._fish_connector.disconnect],
                                                                ["Change", self._change_server_name]],
                                                       "Patch": [["add", self._patch]]}
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
        self._szene_editor.add_szene(self._get_name("Szene Name", "Enter Szene Name:"))

    def _remove_universe(self) -> None:
        """TODO"""
        pass

    def _start_connection(self) -> None:
        """start connection with fish server"""
        self._fish_connector.start()
        self._szene_editor.start()

    def _change_server_name(self) -> None:
        """change fish socket name"""
        self._fish_connector.change_server_name(self._get_name("Server Name", "Enter Server Name:"))

    def _get_file_name(self, title: str):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, "",
                                                             "Text Files (*.txt);;All Files (*)", )
        return file_name

    def _save_scenes(self) -> None:
        """Safes the current scene to a file."""
        xml = createXML(self._board_configuration)
        writeDocument("ShowFile.xml", xml)

    def _load_scenes(self) -> None:
        """load szene from file"""
        file_name = self._get_file_name("load Szene")
        if file_name:
            with open(file_name, "r") as f:
                for (szene_index, line) in enumerate(f):
                    universes = line.split(";")
                    for (universe_index, universe) in enumerate(universes):
                        for (chanel, value) in enumerate(universe.split(",")):
                            self._szene_editor.scenes[szene_index].universes[universe_index].channels[chanel].value \
                                = int(value)

    def _edit_config(self) -> None:
        """Edit the board configuration.
        TODO Implement
        """

    def _patch(self) -> None:
        """ patch a fixture"""
        form = PatchingDialog(self)
        if form.exec():
            self._szene_editor.patch(form.get_used_fixture(), form.patching.text())

    def _get_name(self, title: str, msg: str) -> str:
        """select a new socket name over an input dialog"""
        text, ok = QtWidgets.QInputDialog.getText(self, title, msg)
        if ok:
            return str(text)

    def _setup_toolbar(self) -> None:
        """Adds a toolbar with actions."""
        self._toolbar = self.addToolBar("Mode")
        self._switch_to_direct_mode_button = QtGui.QAction(self)
        self._switch_to_direct_mode_button.setText("Direct Mode")
        self._switch_to_direct_mode_button.triggered.connect(self._switch_to_direct_mode)
        self._toolbar.addAction(self._switch_to_direct_mode_button)

        self._switch_to_filter_mode_button = QtGui.QAction(self)
        self._switch_to_filter_mode_button.setText("Filter Mode")
        self._switch_to_filter_mode_button.triggered.connect(self._switch_to_filter_mode)
        self._toolbar.addAction(self._switch_to_filter_mode_button)

        self.__debug_console = QtGui.QAction(self)
        self.__debug_console.setText("Debug")
        self.__debug_console.triggered.connect(self._switch_to_debug_console)
        self._toolbar.addAction(self.__debug_console)

        self.__send_show_file_action = QtGui.QAction(self)
        self.__send_show_file_action.setText("Send Show File")
        self.__send_show_file_action.triggered.connect(self._send_show_file)

        self.__enter_scene_action = QtGui.QAction(self)
        self.__enter_scene_action.setText("Change Scene")
        self.__enter_scene_action.triggered.connect(self._enter_scene)

    def _switch_to_direct_mode(self) -> None:
        """switch to direct mode"""
        self._widgets.setCurrentIndex(0)
        self._toolbar.removeAction(self.__send_show_file_action)
        self._toolbar.removeAction(self.__enter_scene_action)

    def _switch_to_filter_mode(self) -> None:
        """switch to filter mode"""
        self._widgets.setCurrentIndex(1)
        self._toolbar.addAction(self.__send_show_file_action)
        self._toolbar.addAction(self.__enter_scene_action)

    def _switch_to_debug_console(self) -> None:
        """switch to Debug Console"""
        self._widgets.setCurrentIndex(2)
        self._toolbar.removeAction(self.__send_show_file_action)
        self._toolbar.removeAction(self.__enter_scene_action)

    def _send_show_file(self) -> None:
        xml = createXML(self._board_configuration)
        print(ET.tostring(xml, encoding='utf8', method='xml'))
        #self._fish_connector.load_show_file(xml=xml, goto_default_scene=True)

    def _enter_scene(self) -> None:
        id, ok = QtWidgets.QInputDialog.getInt(self, "Fish: Change scene", "Scene id (0-index)")
        if ok:
            print(f"Switching to scene {id}")
            # self._fish_connector.enter_scene(id)

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

        self._last_cycle_time = [0] * 45
        self._last_cycle_time_widget = QtWidgets.QLabel(str(max(self._last_cycle_time)))

        self._fish_connector.last_cycle_time_update.connect(lambda cycle: self._update_last_cycle_time(cycle))
        status_bar.addWidget(self._last_cycle_time_widget)

    def _update_last_cycle_time(self, new_value: int):
        """update plot of fish last cycle Time"""
        self._last_cycle_time = self._last_cycle_time[1:]  # Remove the first y element.
        self._last_cycle_time.append(new_value)  # Add a new value

        maximum = max(self._last_cycle_time)
        self._last_cycle_time_widget.setText(str(maximum) + " ms")
        match maximum:
            case num if 0 <= num < 15:
                self._last_cycle_time_widget.setStyleSheet(Style.LABEL_OKAY)
            case num if 15 <= num < 19:
                self._last_cycle_time_widget.setStyleSheet(Style.LABEL_WARN)
            case _:
                self._last_cycle_time_widget.setStyleSheet(Style.LABEL_ERROR)


if __name__ == "__main__":
    logging.basicConfig(encoding='utf-8', level=logging.INFO)
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    screen_width = app.primaryScreen().size().width()
    screen_height = app.primaryScreen().size().height()
    widget = MainWindow()
    widget.showMaximized()

    sys.exit(app.exec())
