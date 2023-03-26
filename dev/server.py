import uuid
from PySide6 import QtCore, QtNetwork
import sys


class ServerManager(QtCore.QObject):
    def __init__(self, parent=None):
        super(ServerManager, self).__init__(parent)
        self._server = QtNetwork.QTcpServer(self)
        self._server.newConnection.connect(self._on_new_connection)
        self._clients = {}

    def start(self, address=QtNetwork.QHostAddress.Any, port=9999):
        print(f"Launching: {address}:{port}")
        return self._server.listen(QtNetwork.QHostAddress(address), port)

    @QtCore.Slot()
    def _on_new_connection(self):
        socket = self._server.nextPendingConnection()
        socket.readyRead.connect(self._on_ready_read)
        if socket not in self._clients:
            self._clients[socket] = uuid.uuid4()

    @QtCore.Slot()
    def _on_ready_read(self):
        socket = self.sender()
        message = socket.readAll()
        sender = self._clients[socket]
        print(f"Received: {sender}: {message}")
        socket.write(bytearray("Received", encoding='utf8'))


if __name__ == '__main__':
    app = QtCore.QCoreApplication(sys.argv)
    server = ServerManager()
    if not server.start('127.0.0.1', 9000):
        sys.exit(-1)
    sys.exit(app.exec())
