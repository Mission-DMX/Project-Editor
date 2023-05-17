# coding=utf-8
"""Module to handle connection with real-time software Fish."""
import logging
import queue
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtNetwork

import proto.Console_pb2
import proto.DirectMode_pb2
import proto.FilterMode_pb2
import proto.MessageTypes_pb2
import proto.RealTimeControl_pb2
import proto.UniverseControl_pb2
import varint
from model.universe import Universe

if TYPE_CHECKING:
    from model.control_desk import FaderBank


class NetworkManager(QtCore.QObject):
    """Handles connection to Fish."""
    connection_state_updated: QtCore.Signal = QtCore.Signal(str)
    status_updated: QtCore.Signal = QtCore.Signal(str)
    last_cycle_time_update: QtCore.Signal = QtCore.Signal(int)

    def __init__(self, parent=None) -> None:
        """Inits the network connection.
        Args:
            parent: parent GUI Object
        """
        super().__init__(parent=parent)
        logging.info("generate new Network Manager")
        self._socket: QtNetwork.QLocalSocket = QtNetwork.QLocalSocket()
        self._is_running: bool = False
        self._fish_status: str = ""
        self._server_name = "/tmp/fish.sock"
        self._socket.stateChanged.connect(self._on_state_changed)
        self._socket.errorOccurred.connect(on_error)
        self._socket.readyRead.connect(self._on_ready_read)
        self._message_queue = queue.Queue()

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
            logging.info(f"connect local socket to Server: {self._server_name}")
            self._socket.connectToServer(self._server_name)
            if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
                self._is_running = True

    def disconnect(self) -> None:
        """disconnect from fish socket"""
        logging.info(f"disconnect local socket from Server")
        self._socket.disconnectFromServer()
        self._is_running = False

    def send_universe(self, universe: Universe) -> None:
        """sends the current dmx data of an universes.

        Args:
            universe: universe to send to fish
        """
        msg = proto.DirectMode_pb2.dmx_output(universe_id=universe.universe_proto.id,
                                              channel_data=[channel.value for channel in universe.channels])

        self._send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_DMX_OUTPUT)

    def generate_universe(self, universe: Universe) -> None:
        """send a new universe to the fish socket"""
        self._send_with_format(universe.universe_proto.SerializeToString(), proto.MessageTypes_pb2.MSGT_UNIVERSE)

    def _send_with_format(self, msg: bytearray, msg_type: proto.MessageTypes_pb2.MsgType) -> None:
        """send message in correct format to fish"""
        self._message_queue.put(tuple([msg, msg_type]))
        while not self._message_queue.empty():
            msg, msg_type = self._message_queue.get()
            logging.debug(f"message to send: {msg}")
            if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
                logging.debug(f"send Message to server {msg}")
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
            msg_len = varint.decode_bytes(msg_bytes[1])
            msg = msg_bytes[2:msg_len + 2]
            msg_bytes = msg_bytes[msg_len + 2:]
            match msg_type:
                case proto.MessageTypes_pb2.MSGT_CURRENT_STATE_UPDATE:
                    message: proto.RealTimeControl_pb2.current_state_update = \
                        proto.RealTimeControl_pb2.current_state_update()
                    message.ParseFromString(bytes(msg))
                    self._fish_update(message)
                case proto.MessageTypes_pb2.MSGT_LOG_MESSAGE:
                    message: proto.RealTimeControl_pb2.long_log_update = proto.RealTimeControl_pb2.long_log_update()
                    message.ParseFromString(bytes(msg))
                    self._log_fish(message)

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

    def _on_state_changed(self) -> None:
        """Starts or stops to send messages if the connection state changes."""
        self.connection_state_updated.emit(self.connection_state())

    def connection_state(self) -> str:
        """current connection state
        Returns:
            str: Connected or Not Connected
        """
        if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            return "Connected"
        else:
            return "Not Connected"

    def load_show_file(self, xml: ET.Element, goto_default_scene: bool) -> None:
        msg = proto.FilterMode_pb2.load_show_file(show_data=ET.tostring(xml, encoding='utf8', method='xml'),
                                                  goto_default_scene=goto_default_scene)
        self._send_with_format(msg, proto.MessageTypes_pb2.MSGT_LOAD_SHOW_FILE)

    def enter_scene(self, scene_id: int) -> None:
        msg = proto.FilterMode_pb2.enter_scene(scene_id=scene_id)
        self._send_with_format(msg, proto.MessageTypes_pb2.MSGT_ENTER_SCENE)

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

    def send_desk_update_message(self, msg: proto.Console_pb2.desk_update):
        """send message to update a desk to fish"""
        if not self.is_running:
            return
        self._enqueue_message(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_DESK_UPDATE)


def on_error(error) -> None:
    """logging current error
    Args:
        error: thrown error
    """
    logging.error(error)
