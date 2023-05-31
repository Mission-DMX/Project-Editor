# coding=utf-8
"""Module to handle connection with real-time software Fish."""
import logging
import math
import queue
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import numpy as np
from PySide6 import QtCore, QtNetwork

import proto.Console_pb2
import proto.DirectMode_pb2
import proto.FilterMode_pb2
import proto.MessageTypes_pb2
import proto.RealTimeControl_pb2
import proto.UniverseControl_pb2
import varint
import x_touch
from model.broadcaster import Broadcaster
from model.patching_universe import PatchingUniverse
from model.universe import Universe

if TYPE_CHECKING:
    from view.main_window import MainWindow
    from cli.bankset_command import FaderBank


class NetworkManager(QtCore.QObject):
    """Handles connection to Fish."""
    status_updated: QtCore.Signal = QtCore.Signal(str)
    last_cycle_time_update: QtCore.Signal = QtCore.Signal(int)

    def __init__(self, parent: "MainWindow") -> None:
        """Inits the network connection.
        Args:
            parent: parent GUI Object
        """
        super().__init__(parent=parent)
        logging.info("generate new Network Manager")
        self._broadcaster = Broadcaster()
        self._socket: QtNetwork.QLocalSocket = QtNetwork.QLocalSocket()
        self._message_queue = queue.Queue()

        self._is_running: bool = False
        self._fish_status: str = ""
        self._server_name = "/tmp/fish.sock"
        self._socket.stateChanged.connect(self._on_state_changed)
        self._socket.errorOccurred.connect(on_error)
        self._socket.readyRead.connect(self._on_ready_read)

        self._broadcaster.send_universe.connect(self._generate_universe)
        self._broadcaster.send_universe_value.connect(self._send_universe)
        self._broadcaster.change_run_mode.connect(self.update_state)
        self._broadcaster.view_to_file_editor.connect(
            lambda: self.update_state(proto.RealTimeControl_pb2.RunMode.RM_FILTER))
        self._broadcaster.view_to_console_mode.connect(
            lambda: self.update_state(proto.RealTimeControl_pb2.RunMode.RM_DIRECT))
        self._broadcaster.load_show_file.connect(lambda xml: self.load_show_file(xml, True))

        self._broadcaster.load_show_file.connect(self.load_show_file)
        self._broadcaster.change_active_scene.connect(self.enter_scene)

        x_touch.XTouchMessages(self._broadcaster, self._msg_to_x_touch)

    @property
    def is_running(self) -> bool:
        """is fish socket already running"""
        return self._is_running

    def change_server_name(self, name: str) -> None:
        """change fish socket name

        Args:
            name:  new socket name
        """
        self._server_name = name

    def start(self) -> None:
        """establish connection with current fish socket"""
        if not self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            logging.info("connect local socket to Server: %s", self._server_name)
            self._socket.connectToServer(self._server_name)
            if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
                self._is_running = True

    def disconnect(self) -> None:
        """disconnect from fish socket"""
        logging.info("disconnect local socket from Server")
        self._socket.disconnectFromServer()
        self._is_running = False

    def _send_universe(self, universe: Universe) -> None:
        """sends the current dmx data of an universes.

        Args:
            universe: universe to send to fish
        """
        if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            msg = proto.DirectMode_pb2.dmx_output(universe_id=universe.universe_proto.id,
                                                  channel_data=[channel.value for channel in universe.channels])

            self._send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_DMX_OUTPUT)

    def _generate_universe(self, universe: PatchingUniverse) -> None:
        """send a new universe to the fish socket"""
        if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            self._send_with_format(universe.universe_proto.SerializeToString(), proto.MessageTypes_pb2.MSGT_UNIVERSE)

    def _msg_to_x_touch(self, msg: proto.Console_pb2.button_state_change):
        if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            self._send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_BUTTON_STATE_CHANGE)

    def _send_with_format(self, msg: bytearray, msg_type: proto.MessageTypes_pb2.MsgType) -> None:
        """send message in correct format to fish"""
        self._enqueue_message(msg, msg_type)
        self.push_messages()

    def push_messages(self):
        """This method pushes the queued messages to fish. This method needs to be called from the GUI thread."""
        while not self._message_queue.empty():
            msg, msg_type = self._message_queue.get()
            logging.debug("message to send: %s with type: %s", msg, msg_type)
            if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
                self._socket.write(varint.encode(msg_type) + varint.encode(len(msg)) + msg)
            else:
                logging.error("not Connected with fish server")

    def _enqueue_message(self, msg: bytearray, msg_type: proto.MessageTypes_pb2.MsgType) -> None:
        self._message_queue.put(tuple([msg, msg_type]))

    def _on_ready_read(self) -> None:
        """Processes incoming data."""
        msg_bytes = self._socket.readAll()
        while len(msg_bytes) > 0:
            msg_type = varint.decode_bytes(msg_bytes[0])
            msg_len = varint.decode_bytes(msg_bytes[1:])
            start = 1 + math.ceil(np.log2(msg_len + 1) / 7)
            msg = msg_bytes[start:start + msg_len]
            msg_bytes = msg_bytes[start + msg_len:]
            match msg_type:
                case proto.MessageTypes_pb2.MSGT_CURRENT_STATE_UPDATE:
                    message: proto.RealTimeControl_pb2.current_state_update = proto.RealTimeControl_pb2.current_state_update()
                    message.ParseFromString(bytes(msg))
                    self._fish_update(message)
                case proto.MessageTypes_pb2.MSGT_LOG_MESSAGE:
                    message: proto.RealTimeControl_pb2.long_log_update = proto.RealTimeControl_pb2.long_log_update()
                    message.ParseFromString(bytes(msg))
                    self._log_fish(message)
                case proto.MessageTypes_pb2.MSGT_BUTTON_STATE_CHANGE:
                    message: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change()
                    message.ParseFromString(bytes(msg))
                    self._button_clicked(message)
                case proto.MessageTypes_pb2.MSGT_DESK_UPDATE:
                    message: proto.Console_pb2.desk_update = proto.Console_pb2.desk_update()
                    message.ParseFromString(bytes(msg))
                    self._handle_desk_update(message)
                case proto.MessageTypes_pb2.MSGT_UPDATE_COLUMN:
                    message: proto.Console_pb2.fader_column = proto.Console_pb2.fader_column()
                    message.ParseFromString(bytes(msg))
                    from model.control_desk import BankSet
                    BankSet.handle_column_update_message(message)
                case _:
                    pass

    def _fish_update(self, msg: proto.RealTimeControl_pb2.current_state_update) -> None:
        """
        current state of Fish
        Args:
            msg: message from Fish
        """
        self.last_cycle_time_update.emit(int(msg.last_cycle_time))
        new_message: str = msg.last_error
        if self._fish_status != new_message:
            self.status_updated.emit(new_message)
            self._fish_status = new_message

    def _log_fish(self, msg: proto.RealTimeControl_pb2.long_log_update):
        """
        long log messages from Fish
        Args:
            msg: message from Fish
        """
        match msg.level:
            case proto.RealTimeControl_pb2.LogLevel.LL_INFO:
                logging.info(msg.what)
            case proto.RealTimeControl_pb2.LogLevel.LL_DEBUG:
                logging.debug(msg.what)
            case proto.RealTimeControl_pb2.LogLevel.LL_ERROR:
                logging.error(msg.what)
            case proto.RealTimeControl_pb2.LogLevel.LL_WARNING:
                logging.warning(msg.what)

    def _button_clicked(self, msg: proto.Console_pb2.button_state_change):
        if msg.new_state == proto.Console_pb2.ButtonState.BS_BUTTON_PRESSED:
            match msg.button:
                case proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH:
                    self._broadcaster.view_to_patch_menu.emit()
                case proto.Console_pb2.ButtonCode.BTN_TRACK_EDITSHOW:
                    self._broadcaster.view_to_file_editor.emit()
                case proto.Console_pb2.ButtonCode.BTN_REV_LASTCUE:
                    self._broadcaster.desk_media_rev_pressed.emit()
                case proto.Console_pb2.ButtonCode.BTN_FF_NEXTCUE:
                    self._broadcaster.desk_media_forward_pressed.emit()
                case proto.Console_pb2.ButtonCode.BTN_STOP_STOPCUE:
                    self._broadcaster.desk_media_stop_pressed.emit()
                case proto.Console_pb2.ButtonCode.BTN_PLAY_RUNCUE:
                    self._broadcaster.desk_media_play_pressed.emit()
                case proto.Console_pb2.ButtonCode.BTN_REC_RECFRAME:
                    self._broadcaster.desk_media_rec_pressed.emit()
                case proto.Console_pb2.ButtonCode.BTN_SCRUB_JOGWHEELMODESWITCH:
                    self._broadcaster.desk_media_scrub_pressed.emit()
                case proto.Console_pb2.ButtonCode.BTN_REPLACE_TEMPERATURE:
                    self._broadcaster.view_to_temperature.emit()
                case proto.Console_pb2.ButtonCode.BTN_DROP_COLOR:
                    self._broadcaster.view_to_color.emit()
                case _:
                    pass
        else:
            match msg.button:
                case proto.Console_pb2.ButtonCode.BTN_SCRUB_JOGWHEELMODESWITCH:
                    self._broadcaster.desk_media_scrub_released.emit()
                case _:
                    pass

    def _handle_desk_update(self, msg: proto.Console_pb2.desk_update):
        # TODO handle update of selected column
        if msg.jogwheel_change_since_last_update < 0:
            for i in range(msg.jogwheel_change_since_last_update * -1):
                self._broadcaster.jogwheel_rotated_left.emit()
        else:
            for i in range(msg.jogwheel_change_since_last_update):
                self._broadcaster.jogwheel_rotated_right.emit()
        if msg.selected_column_id:
            self._broadcaster.select_column_id.emit(msg.selected_column_id)
        else:
            self._broadcaster.view_leave_colum_select.emit()
        pass

    def _on_state_changed(self) -> None:
        """Starts or stops to send messages if the connection state changes."""
        self._broadcaster.connection_state_updated.emit(self.connection_state())

    def connection_state(self) -> bool:
        """current connection state
        Returns:
            bool: Connected or Not Connected
        """
        return self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState

    def load_show_file(self, xml: ET.Element, goto_default_scene: bool) -> None:
        """
        Sends show file as xml data to fish
        Args:
            xml: xml data to be sent
            goto_default_scene: scene to be loaded
        """
        msg = proto.FilterMode_pb2.load_show_file(show_data=ET.tostring(xml, encoding='utf8', method='xml'),
                                                  goto_default_scene=goto_default_scene)
        self._send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_LOAD_SHOW_FILE)

    def enter_scene(self, scene_id: int) -> None:
        """
        Tells fish to load a specific scene
        Args:
            scene_id: The scene to be loaded
        """
        msg = proto.FilterMode_pb2.enter_scene(scene_id=scene_id)
        self._send_with_format(msg, proto.MessageTypes_pb2.MSGT_ENTER_SCENE)

    def update_state(self, run_mode: proto.RealTimeControl_pb2.RunMode.ValueType):
        """Changes fish's run mode

        Args:
            run_mode: The new mode
        """
        msg = proto.RealTimeControl_pb2.update_state(new_state=run_mode)
        self._send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_UPDATE_STATE)

    def send_fader_bank_set_delete_message(self, fader_bank_id: str):
        """send message to delete a bank set to fish"""
        delete_msg = proto.Console_pb2.remove_fader_bank_set(bank_id=fader_bank_id)
        self._enqueue_message(delete_msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_REMOVE_FADER_BANK_SET)

    def send_add_fader_bank_set_message(self, bank_id: str, active_bank_index: int, fader_banks: list["FaderBank"]):
        """This method accumulates the content of a bank set and schedules the required messages for an update."""
        add_set_msg = proto.Console_pb2.add_fader_bank_set(bank_id=bank_id, default_active_fader_bank=active_bank_index)
        for bank in fader_banks:
            bank_definition = bank.generate_bank_message()
            add_set_msg.banks.extend([bank_definition])
        self._enqueue_message(add_set_msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_ADD_FADER_BANK_SET)
        for bank in fader_banks:
            bank._pushed_to_device = True
            for col in bank.columns:
                col._pushed_to_device = True

    def send_update_column_message(self, msg: proto.Console_pb2.fader_column):
        """send message to update a column to fish"""
        if not self.is_running:
            return
        self._enqueue_message(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_UPDATE_COLUMN)

    def send_desk_update_message(self, msg: proto.Console_pb2.desk_update, update_from_gui: bool):
        """send message to update a desk to fish"""
        if not self.is_running:
            return
        if update_from_gui:
            self._send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_DESK_UPDATE)
        else:
            self._enqueue_message(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_DESK_UPDATE)


def on_error(error) -> None:
    """logging current error
    Args:
        error: thrown error
    """
    logging.error(error)
