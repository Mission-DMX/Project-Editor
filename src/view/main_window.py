"""main Window for the Editor"""
import os.path
import platform
from typing import TYPE_CHECKING, override

from PySide6 import QtGui, QtWidgets
from PySide6.QtGui import QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import QApplication, QProgressBar, QWidget

import proto.RealTimeControl_pb2
from controller.file.showfile_dialogs import _save_show_file, show_load_showfile_dialog, show_save_showfile_dialog
from controller.network import NetworkManager
from controller.utils.process_notifications import get_global_process_state, get_progress_changed_signal
from model.board_configuration import BoardConfiguration
from model.broadcaster import Broadcaster
from model.control_desk import BankSet, ColorDeskColumn
from style import Style
from utility import resource_path
from view.action_setup_view.combined_action_setup_widget import CombinedActionSetupWidget
from view.console_mode.console_universe_selector import UniverseSelector
from view.dialogs.colum_dialog import ColumnDialog
from view.logging_view.logging_widget import LoggingWidget
from view.main_widget import MainWidget
from view.misc.settings.settings_dialog import SettingsDialog
from view.patch_view.patch_mode import PatchMode
from view.show_mode.editor.showmanager import ShowEditorWidget
from view.show_mode.player.showplayer import ShowPlayerWidget
from view.utility_widgets.wizzards.theater_scene_wizard import TheaterSceneWizard

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent


class MainWindow(QtWidgets.QMainWindow):
    """Main window of the app. All widget are children of its central widget."""

    STATUS_ICON_DIRECT_MODE = QIcon(resource_path(os.path.join("resources", "icons", "faders.svg")))
    STATUS_ICON_FILTER_MODE = QIcon(resource_path(os.path.join("resources", "icons", "play.svg")))

    def __init__(self, parent: QWidget = None) -> None:
        """Inits the MainWindow.

        Args:
            parent: Qt parent of the widget.
        """
        super().__init__(parent)
        # first logging to don't miss logs
        debug_console = LoggingWidget()
        self._broadcaster = Broadcaster()
        self.setWindowTitle("Project-Editor")

        # model objects
        self._fish_connector: NetworkManager = NetworkManager()
        self._board_configuration: BoardConfiguration = BoardConfiguration()

        from model.ui_configuration import setup_network_manager

        setup_network_manager(self._fish_connector, self._broadcaster)

        # views
        views: list[tuple[str, QtWidgets.QWidget, callable]] = [
            ("Console Mode", MainWidget(UniverseSelector(self._board_configuration, self), self),
             lambda: self._to_widget(0)),
            (
                "Editor Mode",
                MainWidget(ShowEditorWidget(self._board_configuration, self._broadcaster, self), self),
                self._broadcaster.view_to_file_editor.emit,
            ),
            (
                "Show Mode",
                MainWidget(ShowPlayerWidget(self._board_configuration, self), self),
                self._broadcaster.view_to_show_player.emit,
            ),
            ("Patch", MainWidget(PatchMode(self._board_configuration, self), self),
             self._broadcaster.view_to_patch_menu.emit),
            ("Debug", debug_console, lambda: self._to_widget(4)),
            (
                "Actions",
                MainWidget(CombinedActionSetupWidget(self, self._broadcaster, self._board_configuration), self),
                self._broadcaster.view_to_action_config.emit,
            ),
        ]

        # select Views
        self._widgets = QtWidgets.QStackedWidget(self)
        self._toolbar = self.addToolBar("Mode")
        for _, view in enumerate(views):
            self._widgets.addWidget(view[1])
            mode_button = QtGui.QAction(view[0], self._toolbar)
            mode_button.triggered.connect(view[2])
            self._toolbar.addAction(mode_button)

        # data_log_window = DmxDataLogWidget(self._broadcaster)
        # self._toolbar.addAction(QtGui.QAction(
        # "dmx_output", self._toolbar, triggered=(lambda: data_log_window.show())))

        self.setCentralWidget(self._widgets)

        self._last_cycle_time = [0] * 45
        self._setup_menubar()
        self._setup_status_bar()

        self._broadcaster.view_to_console_mode.connect(lambda: self._to_widget(0))
        self._broadcaster.view_to_file_editor.connect(lambda: self._to_widget(1))
        self._broadcaster.view_to_show_player.connect(lambda: self._to_widget(2))
        self._broadcaster.view_to_patch_menu.connect(lambda: self._to_widget(3))
        self._broadcaster.select_column_id.connect(self._show_column_dialog)
        self._broadcaster.view_to_color.connect(self._is_column_dialog)
        self._broadcaster.view_to_temperature.connect(self._is_column_dialog)
        self._broadcaster.save_button_pressed.connect(self._save_show)
        self._broadcaster.view_to_action_config.connect(lambda: self._to_widget(5))

        self._fish_connector.start()
        if self._fish_connector:
            from model.control_desk import set_network_manager

            set_network_manager(self._fish_connector)
            self._broadcaster.view_leave_patch_menu.emit()
            self._broadcaster.view_leave_file_editor.emit()
            self._broadcaster.view_leave_show_player.emit()
            self._broadcaster.view_leave_color.emit()
            self._broadcaster.view_leave_temperature.emit()
            self._broadcaster.view_leave_console_mode.emit()
        self._about_window = None
        self._settings_dialog = None
        self._theatre_scene_setup_wizard = None

        self.setWindowIcon(QPixmap(resource_path(os.path.join("resources", "logo.png"))))

    @property
    def fish_connector(self) -> NetworkManager:
        """NetworkManager"""
        return self._fish_connector

    def _to_widget(self, index: int) -> None:
        if self._widgets.currentIndex() == index:
            if self._widgets.currentIndex() == 3:
                self._broadcaster.view_patching.emit()
        else:
            match self._widgets.currentIndex():
                case 0:
                    self._broadcaster.view_leave_console_mode.emit()
                case 1:
                    self._broadcaster.view_leave_file_editor.emit()
                case 2:
                    self._broadcaster.view_leave_show_player.emit()
                case 3:
                    self._broadcaster.view_leave_patch_menu.emit()
                case 4:
                    self._broadcaster.view_leave_action_config.emit()
            self._widgets.setCurrentIndex(index)

    def _setup_menubar(self) -> None:
        """Adds a menubar with submenus."""
        self.setMenuBar(QtWidgets.QMenuBar())
        menus: dict[str, list[tuple[str, None | callable, str | None]]] = {
            "Fish": [
                ("&Connect", self._start_connection, None),
                ("&Disconnect", self._fish_connector.disconnect, None),
                ("Change", self._change_server_name, None),
                ("---", None, None),
                ("&Filter Mode",
                 lambda: self._broadcaster.change_run_mode.emit(proto.RealTimeControl_pb2.RunMode.RM_FILTER), None),
                ("&Direct Mode",
                 lambda: self._broadcaster.change_run_mode.emit(proto.RealTimeControl_pb2.RunMode.RM_DIRECT), None),
                ("---", None, None),
                ("Stop", lambda: self._broadcaster.change_run_mode.emit(proto.RealTimeControl_pb2.RunMode.RM_STOP),
                 None),
            ],
            "File": [
                ("&Load Showfile", lambda: show_load_showfile_dialog(self, self._board_configuration), "O"),
                ("Save Showfile", self._save_show, "S"),
                ("&Save Showfile As", lambda: show_save_showfile_dialog(self, self._board_configuration), "Shift+S"),
                ("---", None, None),
                ("Settings", self.open_show_settings, ","),
            ],
            "Edit": [
                ("&Undo", None, "Z"),  # TODO implement edit history
                ("&Redo", None, "Shift+Z"),
            ],
            # "Show": [
            #    ("Scene Wizard", self._open_scene_setup_wizard, None)
            #    # TODO link wizard that creates a theater scene based on patched fixtures
            # ],
            "Help": [
                ("&About", self._open_about_window, None),
            ],
        }
        for name, entries in menus.items():
            menu: QtWidgets.QMenu = QtWidgets.QMenu(name, self.menuBar())
            self._add_entries_to_menu(menu, entries)
            self.menuBar().addAction(menu.menuAction())

    @override
    def closeEvent(self, event: QCloseEvent, /) -> None:
        # TODO use event.ignore() here is there's still stuff to do
        super().closeEvent(event)
        QApplication.processEvents()
        self._broadcaster.application_closing.emit()
        QApplication.processEvents()

    def _start_connection(self) -> None:  # TODO rework to signals
        self._fish_connector.start(True)

    def _add_entries_to_menu(self, menu: QtWidgets.QMenu, entries: list[list[str, callable]]) -> None:
        """add entries to a menu"""
        for entry in entries:
            if entry[0] == "---":
                menu.addSeparator()
                continue
            menu_entry: QtGui.QAction = QtGui.QAction(entry[0], self)
            if entry[1] is not None:
                menu_entry.triggered.connect(entry[1])
            else:
                menu_entry.setEnabled(False)
            if entry[2] is not None:
                menu_entry.setShortcut(QKeySequence(("Cmd+" if platform.system() == "Darwin" else "Ctrl+") + entry[2]))
            menu.addAction(menu_entry)

    def _change_server_name(self) -> None:
        """change fish socket name"""
        text, run = QtWidgets.QInputDialog.getText(self, "Server Name", "Enter Server Name:")
        if run:
            self._fish_connector.change_server_name(text)

    def _setup_status_bar(self) -> None:
        """build status bor"""
        status_bar = QtWidgets.QStatusBar()
        status_bar.setMaximumHeight(50)
        self.setStatusBar(status_bar)

        self._status_runmode = QtWidgets.QLabel()
        self._fish_connector.run_mode_changed.connect(self._fish_run_mode_changed)
        status_bar.addWidget(self._status_runmode)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setLineWidth(3)
        separator.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        status_bar.addWidget(separator)

        self._status_pbar = QProgressBar(parent=status_bar)
        self._status_pbar.setVisible(False)
        self._status_pbar.setMinimumWidth(50)
        status_bar.addWidget(self._status_pbar)

        self._status_current_scene_label = QtWidgets.QLabel("")
        self._fish_connector.active_scene_on_fish_changed.connect(
            lambda i: self._status_current_scene_label.setText(
                f"[{i}] {self._board_configuration.get_scene_by_id(i).human_readable_name if
                i != -1 and self._board_configuration.get_scene_by_id(i) is not None else ''}"))
        status_bar.addWidget(self._status_current_scene_label)

        self._label_state_update = QtWidgets.QLabel("", status_bar)  # TODO start Value
        self._broadcaster.connection_state_updated.connect(self._fish_state_update)
        get_progress_changed_signal().connect(self._proccess_status_listener)
        status_bar.addWidget(self._label_state_update)

        label_last_error = QtWidgets.QLabel("Error", status_bar)
        self._fish_connector.status_updated.connect(label_last_error.setText)
        status_bar.addWidget(label_last_error)

        self._last_cycle_time_widget = QtWidgets.QLabel(str(max(self._last_cycle_time)))

        self._fish_connector.last_cycle_time_update.connect(self._update_last_cycle_time)
        status_bar.addWidget(self._last_cycle_time_widget)

    def _proccess_status_listener(self) -> None:
        c, m = get_global_process_state()
        self._status_pbar.setVisible(c != m)
        self._status_pbar.setValue(int((c / m) * 100))

    def _fish_run_mode_changed(self, new_run_mode: int) -> None:
        if new_run_mode == proto.RealTimeControl_pb2.RunMode.RM_FILTER:
            self._status_current_scene_label.setVisible(True)
            self._status_runmode.setPixmap(MainWindow.STATUS_ICON_FILTER_MODE.pixmap(16, 16))
        else:
            self._status_current_scene_label.setVisible(False)
            self._status_runmode.setPixmap(MainWindow.STATUS_ICON_DIRECT_MODE.pixmap(16, 16))

    def _fish_state_update(self, connected: bool) -> None:
        if connected:
            self._label_state_update.setText("Connected")
            self._last_cycle_time_widget.setVisible(True)
        else:
            self._label_state_update.setText("Not Connected")
            self._last_cycle_time_widget.setVisible(False)

    def _update_last_cycle_time(self, new_value: int) -> None:
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

    def _show_column_dialog(self, index: str) -> None:
        """Dialog modify tho selected Column"""
        active_bank_set = BankSet.active_bank_set()
        column = active_bank_set.get_column(index)
        if active_bank_set.active_column != column:
            if active_bank_set.active_column:
                self._broadcaster.view_change_colum_select.emit()
            active_bank_set.set_active_column(column)
            if isinstance(column, ColorDeskColumn):
                column_dialog = ColumnDialog(column)
                column_dialog.finished.connect(BankSet.push_messages_now)
                column_dialog.show()

    def _is_column_dialog(self) -> None:
        if not BankSet.active_bank_set():
            self._broadcaster.view_leave_color.emit()
            self._broadcaster.view_leave_temperature.emit()
            return
        if not BankSet.active_bank_set().active_column:
            self._broadcaster.view_leave_color.emit()
            self._broadcaster.view_leave_temperature.emit()

    def _save_show(self) -> None:
        if self._board_configuration:
            if self._board_configuration.file_path:
                _save_show_file(self._board_configuration.file_path, self._board_configuration)
            else:
                show_save_showfile_dialog(self, self._board_configuration)

    def _open_about_window(self) -> None:
        if not self._about_window:
            from view.misc.about_window import AboutWindow
            self._about_window = AboutWindow(self)
        self._about_window.show()

    @property
    def show_configuration(self) -> BoardConfiguration:
        return self._board_configuration

    def open_show_settings(self) -> None:
        self._settings_dialog = SettingsDialog(self, self._board_configuration)
        self._settings_dialog.show()

    def _open_scene_setup_wizard(self) -> None:
        self._theatre_scene_setup_wizard = TheaterSceneWizard(self, self.show_configuration)
        self._theatre_scene_setup_wizard.show()
