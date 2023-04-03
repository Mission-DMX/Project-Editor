"""Module to handle connection with real-time software Fish."""
import logging

from PySide6 import QtCore, QtNetwork

import varint
import proto.MessageTypes_pb2
import proto.DirectMode_pb2
import proto.UniverseControl_pb2

from DMXModel import Universe


class NetworkManager(QtCore.QObject):
    """Handles connection to Fish.

    Sends the current data of a universe
    """

    def __init__(self, parent=None):
        """Inits the network connection.
        """
        super().__init__(parent=parent)
        logging.info("generate new Network Manager")
        self._socket: QtNetwork.QLocalSocket = QtNetwork.QLocalSocket()
#        self._socket.setServerName("/var/run/fish.sock")
        self._socket.setServerName("/tmp/fish.sock")
        self._socket.stateChanged.connect(self._on_state_changed)
        self._socket.errorOccurred.connect(on_error)
        self._socket.readyRead.connect(self.on_ready_read)

    def start(self):
        """Establishes the connection.
        """
        logging.info(f"connect local socket to Server")
        self._socket.connectToServer()

    def _on_state_changed(self, state):
        """Starts or stops to send messages if the connection state changes.
        Args:
            state: The connection state of the current connection.
        """
        logging.warning(f"connection change to {str(self._socket.state())}")

    def send_universe(self, universe: Universe) -> None:
        """
        Sends the current dmx data of an universes.#

        :param universe: universe to send to fish
        """
        msg = proto.DirectMode_pb2.dmx_output(universe_id=universe.address,
                                              channel_data=[channel.value for channel in universe.channels])

        self.send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_DMX_OUTPUT)

    def generate_universe(self, universe: Universe) -> None:
        print(self._socket.state())
        # if self._socket.state() == QtNetwork.QAbstractSocket.SocketState.ConnectedState:
        msg = proto.UniverseControl_pb2.Universe(id=1,
                                                 remote_location=proto.UniverseControl_pb2.Universe.ArtNet(
                                                     ip_address="192.168.0.2",
                                                     port=6454,
                                                     universe_on_device=1
                                                 ))
        self.send_with_format(msg.SerializeToString(), proto.MessageTypes_pb2.MSGT_UNIVERSE)

    def send_with_format(self, msg: bytearray, msg_type: proto.MessageTypes_pb2.MsgType):
        logging.debug(f"message to send: {msg}")
        if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            logging.info(f"send Message to server {msg}")
            self._socket.write(varint.encode(msg_type) + varint.encode(len(msg)) + msg)
        else:
            logging.error("not Connected with fish server")

    def on_ready_read(self):
        """Processes incoming data."""
        logging.debug(f"Response: {self._socket.readAll()}")


def on_error(error):
    logging.error(error)
