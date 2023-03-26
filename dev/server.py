import uuid
from PySide6 import QtCore, QtNetwork
import sys


class ServerManager(QtCore.QObject):
    def __init__(self, parent=None):
        super(ServerManager, self).__init__(parent)
        self._server = QtNetwork.QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)
        self._clients = {}



    def start(self):
        print("[DEV] Launching FishServer")
        return self._server.listen("FishServer")

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
    if not server.start():
        sys.exit(-1)
    sys.exit(app.exec())
