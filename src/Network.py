"""Module to handle connection with real-time software Fish."""

from PySide6 import QtCore, QtNetwork

import proto.DirectMode_pb2
from DMXModel import Universe


class NetworkManager(QtCore.QObject):
    """Handles connection to Fish.

    Sends the current data of all universes every message_interval milliseconds.
    """

    def __init__(self, universes: list[Universe], message_interval: int = 1000, parent=None):
        """Inits the network connection.

        Args:
            universes: List of active universes.
            message_interval: Time in milliseconds to wait between sending universe info.
        """
        super().__init__(parent=parent)

        self._APPID = "FishServer"

        self._universes = universes

        self._socket: QtNetwork.QLocalSocket = QtNetwork.QLocalSocket(self)
        self._socket.stateChanged.connect(self._on_state_changed)
        self._socket.readyRead.connect(self.on_ready_read)
        self._timer: QtCore.QTimer = QtCore.QTimer(self)
        self._timer.setInterval(message_interval)
        self._timer.timeout.connect(self._send)

    def start(self, appid: str = ""):
        """Establishes the connection.

        Args:
            address: Address of Fish software host. Must be parseable to be QtNetwork.QHostAddress.
            port: Port of Fish software.
        """
        self._socket.connectToServer(self._APPID)

    @QtCore.Slot(QtNetwork.QLocalSocket.LocalSocketState)
    def _on_state_changed(self, state):
        """Starts or stops to send messages if the connection state changes.

        Args:
            state: The connection state of the current connection.
        """
        if state == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            self._timer.start()
            print(f"Connected to {self._socket.serverName()}.")
        elif state == QtNetwork.QLocalSocket.LocalSocketState.UnconnectedState:
            print(f"Disconnected from {self._socket.serverName()}.")

    @QtCore.Slot()
    def _send(self):
        """Sends the current dmx data of all universes."""
        if self._socket.state() == QtNetwork.QLocalSocket.LocalSocketState.ConnectedState:
            for universe in self._universes:
                msg = proto.DirectMode_pb2.dmx_output(universe_id=universe.address,
                                                      channel_data=[channel.value for channel in universe.channels])
                self._socket.write(bytearray(str(msg), encoding='utf8'))

    @QtCore.Slot()
    def on_ready_read(self):
        """Processes incoming data."""
        print(f"Response: {self._socket.readAll()}")
