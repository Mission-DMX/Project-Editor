# coding=utf-8
"""main Window for the Editor"""

from PySide6 import QtWidgets, QtGui

from Style import Style
from model.board_configuration import BoardConfiguration
from model.broadcaster import Broadcaster
from network import NetworkManager
from view.console_mode.console_scene_selector import ConsoleSceneSelector
from view.logging_mode.logging_widget import LoggingWidget
from view.main_widget import MainWidget
from view.patch_mode.patch_mode import PatchMode
from view.show_mode.node_editor import NodeEditorWidget


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
        self._broadcaster = Broadcaster()
        Broadcaster.last_instance = self._broadcaster
        self.setWindowTitle("Project-Editor")

        # model objects
        self._fish_connector: NetworkManager = NetworkManager(self._broadcaster, self)
        self._board_configuration: BoardConfiguration = BoardConfiguration(self._broadcaster)

        # views
        views: list[tuple[str, QtWidgets.QWidget, callable]] = [
            ("Console Mode", MainWidget(ConsoleSceneSelector(self._broadcaster, self), self),
             lambda: self._to_widget(0)),
            ("Filter Mode", MainWidget(NodeEditorWidget(self, self._board_configuration, self._broadcaster), self),
             lambda: self._broadcaster.view_to_file_editor.emit()),
            ("Patch", MainWidget(PatchMode(self._broadcaster, self), self),
             lambda: self._broadcaster.view_to_patch_menu.emit()),
            ("Debug", debug_console, lambda: self._to_widget(3))]

        # select Views
        self._widgets = QtWidgets.QStackedWidget(self)
        self._toolbar = self.addToolBar("Mode")
        for index, view in enumerate(views):
            self._widgets.addWidget(view[1])
            mode_button = QtGui.QAction(view[0], self._toolbar)
            mode_button.triggered.connect(view[2])
            self._toolbar.addAction(mode_button)

        self.setCentralWidget(self._widgets)

        self._last_cycle_time = [0] * 45
        self._setup_menubar()
        self._setup_status_bar()

        self._broadcaster.view_to_patch_menu.connect(lambda: self._to_widget(2))
        self._broadcaster.view_to_file_editor.connect(lambda: self._to_widget(1))

        self._fish_connector.start()
        if self._fish_connector:
            from model.control_desk import set_network_manager
            set_network_manager(self._fish_connector)

    def _to_widget(self, index: int) -> None:
        if self._widgets.currentIndex() == index:
            if self._widgets.currentIndex() == 2:
                self._broadcaster.view_patching.emit()
        else:
            if self._widgets.currentIndex() == 1:
                self._broadcaster.view_leave_file_editor.emit()
            if self._widgets.currentIndex() == 2:
                self._broadcaster.view_leave_patch_menu.emit()
            self._widgets.setCurrentIndex(index)

    def _setup_menubar(self) -> None:
        """Adds a menubar with submenus."""
        self.setMenuBar(QtWidgets.QMenuBar())
        menus: dict[str, list[list[str, callable]]] = {
            "Fish": [["Connect", self._start_connection], ["Disconnect", self._fish_connector.disconnect],
                     ["Change", self._change_server_name]]}
        for name, entries in menus.items():
            menu: QtWidgets.QMenu = QtWidgets.QMenu(name, self.menuBar())
            self._add_entries_to_menu(menu, entries)
            self.menuBar().addAction(menu.menuAction())

    def _start_connection(self):  # TODO rework to signals
        self._fish_connector.start()
        from model.control_desk import commit_all_bank_sets
        commit_all_bank_sets()

    def _add_entries_to_menu(self, menu: QtWidgets.QMenu, entries: list[list[str, callable]]) -> None:
        """ add entries to a menu"""
        for entry in entries:
            menu_entry: QtGui.QAction = QtGui.QAction(entry[0], self)
            menu_entry.triggered.connect(entry[1])
            menu.addAction(menu_entry)

    def _change_server_name(self) -> None:
        """change fish socket name"""
        text, run = QtWidgets.QInputDialog.getText(self, "Server Name", "Enter Server Name:")
        if run:
            self._fish_connector.change_server_name(text)

    def _setup_status_bar(self) -> None:
        """ build status bor"""
        status_bar = QtWidgets.QStatusBar()
        status_bar.setMaximumHeight(50)
        self.setStatusBar(status_bar)

        self._label_state_update = QtWidgets.QLabel("", status_bar)  # TODO start Value
        self._broadcaster.connection_state_updated.connect(self._fish_state_update)
        status_bar.addWidget(self._label_state_update)

        label_last_error = QtWidgets.QLabel("Error", status_bar)
        self._fish_connector.status_updated.connect(label_last_error.setText)
        status_bar.addWidget(label_last_error)

        self._last_cycle_time_widget = QtWidgets.QLabel(str(max(self._last_cycle_time)))

        self._fish_connector.last_cycle_time_update.connect(self._update_last_cycle_time)
        status_bar.addWidget(self._last_cycle_time_widget)

    def _fish_state_update(self, connected: bool):
        if connected:
            self._label_state_update.setText("Connected")
            self._last_cycle_time_widget.setVisible(True)
        else:
            self._label_state_update.setText("Not Connected")
            self._last_cycle_time_widget.setVisible(False)

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
