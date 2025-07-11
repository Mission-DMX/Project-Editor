"""Classes for remote connection"""
from asyncio import IncompleteReadError
from logging import getLogger
from socket import AF_INET6, SOCK_STREAM, socket
from threading import Thread

from controller.cli.cli_context import CLIContext
from controller.network import NetworkManager
from model import BoardConfiguration

logger = getLogger(__name__)


class SocketStreamReader:
    """This class is used to split the input TCP stream into separate lines."""

    def __init__(self, sock: socket) -> None:
        """Initialize the stream reader

        Arguments:
        sock -- the socket to listen on
        """
        self._sock = sock
        self._recv_buffer = bytearray()
        self.echo = True

    def read(self, num_bytes: int = -1) -> bytes:
        """This method is here to comply with the stream interface but never, hence not implemented"""
        raise NotImplementedError

    def read_exactly(self, num_bytes: int) -> bytes:
        """Read num_bytes from the socket."""
        buf = bytearray(num_bytes)
        pos = 0
        while pos < num_bytes:
            n = self._recv_into(memoryview(buf)[pos:])
            if n == 0:
                raise IncompleteReadError(bytes(buf[:pos]), num_bytes)
            pos += n
        return bytes(buf)

    def readline(self) -> bytes:
        """Read an entire line from the socket stream.

        Returns:
        bytearray with line.
        """
        return self.read_until(b"\n")

    def read_until(self, separator: bytes = b"\n") -> bytes:
        """Read from the socket until the escape sequence was found

        Arguments:
        separator -- the delimiter to look out for

        Returns:
        bytearray with the found content.
        """
        if len(separator) != 1:
            raise ValueError("Only separators of length 1 are supported.")

        chunk = bytearray(4096)
        start = 0
        buf = bytearray(len(self._recv_buffer))
        bytes_read = self._recv_into(memoryview(buf))
        if bytes_read != len(buf):
            raise ValueError("Not enough bytes to read.")

        while True:
            idx = buf.find(separator, start)
            if idx != -1:
                break

            start = len(self._recv_buffer)
            bytes_read = self._recv_into(memoryview(chunk))
            buf += memoryview(chunk)[:bytes_read]

        result = bytes(buf[: idx + 1])
        self._recv_buffer = b"".join(
            (memoryview(buf)[(idx + 1):], self._recv_buffer),
        )
        return result

    def _recv_into(self, view: memoryview) -> int:
        """This method performs a zero copy read request."""
        bytes_read = min(len(view), len(self._recv_buffer))
        view[:bytes_read] = self._recv_buffer[:bytes_read]
        self._recv_buffer = self._recv_buffer[bytes_read:]
        if bytes_read == len(view):
            return bytes_read
        bytes_read_prior = bytes_read
        bytes_read += self._sock.recv_into(view[bytes_read:])
        if self.echo:
            self._sock.send(self._recv_buffer[bytes_read_prior:bytes_read])
        return bytes_read


class Connection:
    """This class handles a remote CLI connection."""

    def __init__(self, client: socket, address: str, connection_map: dict, show: BoardConfiguration,
                 networkmgr: "NetworkManager") -> None:
        """This constructor takes over the connection.

        Arguments:
        client -- the connection socket fd.
        address -- the remote address of the connected client.
        connection_map -- the map handling all active connections.
        """
        self.context = CLIContext(show, networkmgr, exit_available=True)
        self._client = client
        self._remote_address = address
        self._connection_map = connection_map
        self._client_thread = Thread(target=self.run)
        self._client_thread.start()

    def run(self) -> None:
        """This method will be called by the client thread in order to handle the client."""
        try:
            logger.info("Got incoming remote CLI connection from %s.", self._remote_address)
            reader = SocketStreamReader(self._client)
            while not self.context.exit_called:
                self._client.send(b"> ")
                line = reader.readline().decode().replace("\r", "").replace("\n", "")
                if line == "@echo off":
                    reader.echo = False
                else:
                    self.context.exec_command(line)
                self._client.send(self.context.fetch_print_buffer().encode())
        except OSError:
            pass
        except UnicodeDecodeError as e:
            self._client.send("Unable to decode command. Exiting.")
            self._client.close()
            logger.exception("Failed to decode CLI command. %s", e)
        finally:
            self._client.close()
        self._connection_map.pop(self._remote_address)

    def stop(self) -> None:
        """Forcefully disconnect and stop the client.

        This operation may block until the operating system released the socket.
        """
        self.context.exit_called = True
        self._client.close()
        self._client_thread.join()

    @property
    def remote_address(self) -> str:
        """Property for remote address"""
        return self._remote_address


class RemoteCLIServer:
    """This class handles the control port. Only IPv6 connections are supported."""

    def __init__(self, show: BoardConfiguration, netmgr: NetworkManager, interface: str = "::",
                 port: int = 2929) -> None:
        """Construct the handler and opens a port.

        Arguments:
        interface -- The interface to bind to. Defaults to all IPv6 interfaces.
        port -- The port to listen on. Defaults to TCP/2929
        """
        self._server_thread = Thread(target=self.run)
        self._bind_interface = interface
        self._bind_port = port
        self._stopped = False
        self._server_socket: socket = None
        self._connected_clients = {}
        self._show = show
        self._network_manager = netmgr
        self._server_thread.start()
        logger.warning("Opened up CLI interface on [%s]:%s", interface, port)

    def run(self) -> None:
        """This method will be run by the server thread in order to process incoming clients."""
        with socket(AF_INET6, SOCK_STREAM) as s:
            self._server_socket = s
            s.bind((self._bind_interface, self._bind_port))
            s.settimeout(2)
            s.listen()
            while not self._stopped:
                try:
                    client, remote_address = s.accept()
                    remote_address = str(remote_address)
                    self._connected_clients[remote_address] = Connection(client, remote_address,
                                                                         self._connected_clients,
                                                                         self._show, self._network_manager)
                except TimeoutError:
                    pass
                except OSError as e:
                    logger.exception("CLI socket error: %s", e)
            s.close()
        logger.info("Exiting CLI server thread")

    def stop(self) -> None:
        """This method stops the server and disconnects all clients.

        It may block until the operating system released all resources.
        """
        logger.info("Stopping CLI server")
        self._stopped = True
        self._server_socket.close()
        to_be_stopped: list[Connection] = [self._connected_clients[k_addr] for k_addr in self._connected_clients]
        for c in to_be_stopped:
            c.stop()
            logger.info("CLI clients from %s disconnected.", c.remote_address)
        try:
            self._server_thread.join()
        except KeyboardInterrupt:
            logger.warning("Shutdown of remote control network socket interrupted by keyboard signal.")
