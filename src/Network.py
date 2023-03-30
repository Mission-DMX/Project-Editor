"""Module to handle connection with real-time software Fish."""

from PySide6 import QtCore, QtNetwork

import proto
import varint
from DMXModel import Universe


class NetworkManager(QtCore.QObject):
    """Handles connection to Fish.

    Sends the current data of a universe
    """

    def __init__(self, parent=None):
        """Inits the network connection.
        """
        super().__init__(parent=parent)

        self._socket: QtNetwork.QLocalSocket = QtNetwork.QLocalSocket()
#        self._socket.setServerName("/var/run/fish.sock")
        self._socket.setServerName("/tmp/fish.sock")
        self._socket.stateChanged.connect(self._on_state_changed)
        self._socket.errorOccurred.connect(self.on_error)
        self._socket.readyRead.connect(self.on_ready_read)

    def start(self):
        """Establishes the connection.
        """
        self._socket.connectToServer()

    def _on_state_changed(self, state):
        """Starts or stops to send messages if the connection state changes.

        Args:
            state: The connection state of the current connection.
        """
        print(f"connection change to {str(self._socket.state())}")

    def on_error(self, error):
        print(error)

    def send(self, universe: Universe) -> None:
        """
        Sends the current dmx data of an universes.#

        :param universe: universe to send to fish
        """
        if self._socket.state() == QtNetwork.QAbstractSocket.SocketState.ConnectedState:
            msg = proto.DirectMode_pb2.dmx_output(universe_id=universe.address,
                                                  channel_data=[channel.value for channel in universe.channels])
            self._socket.write(bytearray(str(msg), encoding='utf8'))

    def _read(self) -> QtCore.QByteArray:
        return self._socket.readAll()

    def on_ready_read(self):
        """Processes incoming data."""
        print(f"Response: {self._socket.readAll()}")
