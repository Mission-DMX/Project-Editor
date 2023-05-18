# coding=utf-8
"""main Window for the Editor"""
from PySide6 import QtWidgets, QtGui

from DMXModel import BoardConfiguration
from Network import NetworkManager
from ShowFile import createXML, writeDocument
from src.Style import Style
from view.main_widget import MainWidget
from view.patching.patching_selector import PatchingSelector
from widgets.Logging.logging_widget import LoggingWidget
from widgets.NodeEditor.NodeEditor import NodeEditorWidget


class MainWindow(QtWidgets.QMainWindow):
    """Main window of the app. All widget are children of its central widget."""

    def __init__(self, parent=None) -> None:
        """Inits the MainWindow.

        Args:
            parent: Qt parent of the widget.
        """
        super().__init__(parent)
        # first logging to don't miss logs
        debug_console = LoggingWidget()

        self.setWindowTitle("Project-Editor")

        # model objects
        self._fish_connector: NetworkManager = NetworkManager()
        self._fish_connector.start()
        self._board_configuration: BoardConfiguration = BoardConfiguration()

        # views
        views: list[tuple[str, QtWidgets]] = [("Patch", MainWidget(PatchingSelector(self), self)),
                                              ("Filter Mode", NodeEditorWidget(self, self._board_configuration)),
                                              ("Debug", debug_console)]
        # TODO  append self._toolbar.addAction(self.__send_show_file_action)
        #  self._toolbar.addAction(self.__enter_scene_action)

        # select Views
        self._widgets = QtWidgets.QStackedWidget(self)
        self._toolbar = self.addToolBar("Mode")
        for index, view in enumerate(views):
            self._widgets.addWidget(view[1])
            mode_button = QtGui.QAction(view[0], self._toolbar)
            mode_button.triggered.connect(lambda *args, i=index: self._widgets.setCurrentIndex(index))
            self._toolbar.addAction(mode_button)

        self.setCentralWidget(self._widgets)

        self._setup_menubar()
        self._setup_status_bar()

    @property
    def fish_connector(self) -> NetworkManager:
        """fish connection Manager"""
        return self._fish_connector

    def _setup_menubar(self) -> None:
        """Adds a menubar with submenus."""
        self.setMenuBar(QtWidgets.QMenuBar())
        menus: dict[str, list[list[str, callable]]] = {"File": [["save", self._save_scenes],
                                                                ["load", self._load_scenes],
                                                                ["Config", self._edit_config]],
                                                       # "Universe": [["add", self._scene_editor.add_universe],
                                                       #             ["remove", self._remove_universe]],
                                                       "Fish": [["Connect", self._fish_connector.start],
                                                                ["Disconnect", self._fish_connector.disconnect],
                                                                ["Change", self._change_server_name]]
                                                       }
        for name, entries in menus.items():
            menu: QtWidgets.QMenu = QtWidgets.QMenu(name, self.menuBar())
            self._add_entries_to_menu(menu, entries)
            self.menuBar().addAction(menu.menuAction())

    def _add_entries_to_menu(self, menu: QtWidgets.QMenu, entries: list[list[str, callable]]) -> None:
        """ add entries to a menu"""
        for entry in entries:
            menu_entry: QtGui.QAction = QtGui.QAction(entry[0], self)
            menu_entry.triggered.connect(entry[1])
            menu.addAction(menu_entry)

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
                            self._scene_editor.scenes[szene_index].universes[universe_index].channels[chanel].value \
                                = int(value)

    def _edit_config(self) -> None:
        """Edit the board configuration.
        TODO Implement
        """

    def _get_name(self, title: str, msg: str) -> str:
        """select a new socket name over an input dialog"""
        text, ok = QtWidgets.QInputDialog.getText(self, title, msg)
        if ok:
            return str(text)

    def _send_show_file(self) -> None:
        xml = createXML(self._board_configuration)
        self._fish_connector.load_show_file(xml=xml, goto_default_scene=True)

    def _setup_status_bar(self) -> None:
        """ build status bor"""
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
