"""Module to handle connection with real-time software Fish."""
import logging

from PySide6 import QtCore, QtNetwork

import proto.DirectMode_pb2
import proto.FilterMode_pb2
import proto.MessageTypes_pb2
import proto.RealTimeControl_pb2
import proto.UniverseControl_pb2
import varint
from DMXModel import Universe


class NetworkManager(QtCore.QObject):
    """Handles connection to Fish.

    Sends the current data of a universe
    """
    connection_state_updated: QtCore.Signal = QtCore.Signal(str)
    status_updated: QtCore.Signal = QtCore.Signal(str)
    last_cycle_time_update: QtCore.Signal = QtCore.Signal(int)

    def __init__(self, parent=None):
        """Inits the network connection.
        """
        super().__init__(parent=parent)
        logging.info("generate new Network Manager")
        self._socket: QtNetwork.QLocalSocket = QtNetwork.QLocalSocket()
        self._already_started: bool = False
        self._fish_status: str = ""
        self._server_name = "/tmp/fish.sock"
        self._socket.stateChanged.connect(self._on_state_changed)
        self._socket.errorOccurred.connect(on_error)
        self._socket.readyRead.connect(self._on_ready_read)

    @property
    def already_started(self) -> bool:
        return self._already_started

    def change_server_name(self, name: str) -> None:
        self._server_name = name

    def start(self) -> None:
        """Establishes the connection.
        """
        if not self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            logging.info(f"connect local socket to Server: {self._server_name}")
            self._socket.connectToServer(self._server_name)
            if self._socket.state == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
                self._already_started = True

    def disconnect(self) -> None:
        logging.info(f"disconnect local socket from Server")
        self._socket.disconnectFromServer()
        self._already_started = False

    def send_universe(self, universe: Universe) -> None:
        """
        Sends the current dmx data of an universes.#

        :param universe: universe to send to fish
        """
        msg = proto.DirectMode_pb2.dmx_output(universe_id=universe.address,
                                              channel_data=[channel.value for channel in universe.channels])

        self._send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_DMX_OUTPUT)

    def generate_universe(self, universe: Universe) -> None:
        msg = proto.UniverseControl_pb2.Universe(id=universe.address,
                                                 remote_location=proto.UniverseControl_pb2.Universe.ArtNet(
                                                     ip_address="10.0.15.1",
                                                     port=6454,
                                                     universe_on_device=universe.address
                                                 ))
        self._send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_UNIVERSE)

    def _send_with_format(self, msg: bytearray, msg_type: proto.MessageTypes_pb2.MsgType) -> None:
        logging.debug(f"message to send: {msg}")
        if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            logging.info(f"send Message to server {msg}")
            self._socket.write(varint.encode(msg_type) + varint.encode(len(msg)) + msg)
        else:
            logging.error("not Connected with fish server")

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
                    update: proto.RealTimeControl_pb2.current_state_update = \
                        proto.RealTimeControl_pb2.current_state_update()
                    update.ParseFromString(bytes(msg))
                    self._fish_update(update)
                case _:
                    pass

    def _fish_update(self, msg: proto.RealTimeControl_pb2.current_state_update) -> None:
        self.last_cycle_time_update.emit(int(msg.last_cycle_time))
        new_message: str = msg.last_error
        if self._fish_status != new_message:
            self.status_updated.emit(new_message)
            self._fish_status = new_message

    def _on_state_changed(self) -> None:
        """Starts or stops to send messages if the connection state changes.
        Args:
            state: The connection state of the current connection.
        """
        self.connection_state_updated.emit(self.connection_state())

    def connection_state(self) -> str:
        if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            return "connected"
        else:
            return "not connected"


def on_error(error):
    logging.error(error)
