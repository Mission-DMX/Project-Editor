# coding=utf-8
"""Classes for remote connection"""
from asyncio import IncompleteReadError
from socket import AF_INET6, SOCK_STREAM
from socket import error as socket_error
from socket import socket
from threading import Thread

from controller.cli.cli_context import CLIContext


class SocketStreamReader:
    """This class is used to split the input TCP stream into separate lines."""
    def __init__(self, sock: socket):
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
        assert bytes_read == len(buf)

        while True:
            idx = buf.find(separator, start)
            if idx != -1:
                break

            start = len(self._recv_buffer)
            bytes_read = self._recv_into(memoryview(chunk))
            buf += memoryview(chunk)[:bytes_read]

        result = bytes(buf[: idx + 1])
        self._recv_buffer = b"".join(
            (memoryview(buf)[(idx + 1):], self._recv_buffer)
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
    def __init__(self, client: socket, address: str, connection_map: dict):
        """This constructor takes over the connection.
        
        Arguments:
        client -- the connection socket fd.
        address -- the remote address of the connected client.
        connection_map -- the map handling all active connections.
        """
        self.context = CLIContext(exit_available=True)
        self._client = client
        self._remote_address = address
        self._connection_map = connection_map
        self._client_thread = Thread(target=self.run)
        self._client_thread.start()

    def run(self):
        """This method will be called by the client thread in order to handle the client."""
        try:
            reader = SocketStreamReader(self._client)
            while not self.context.exit_called:
                self._client.send("> ".encode("utf-8"))
                line = reader.readline().decode("utf-8").replace("\r", "").replace("\n", "")
                if line == "@echo off":
                    reader.echo = False
                else:
                    self.context.exec_command(line)
                self._client.send(self.context.fetch_print_buffer().encode("utf-8"))
        except socket_error:
            pass
        finally:
            self._client.close()
        self._connection_map.pop(self._remote_address)

    def stop(self):
        """Forcefully disconnect and stop the client.
        
        This operation may block until the operating system released the socket.
        """
        self.context.exit_called = True
        self._client.close()
        self._client_thread.join()


class RemoteCLIServer:
    """This class handles the control port. Only IPv6 connections are supported."""
    
    def __init__(self, interface: str = "::", port: int = 2929):
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
        self._connected_clients = dict()
        self._server_thread.start()

    def run(self):
        """This method will be run by the server thread in order to process incoming clients."""
        with socket(AF_INET6, SOCK_STREAM) as s:
            self._server_socket = s
            s.bind((self._bind_interface, self._bind_port))
            s.listen()
            while not self._stopped:
                try:
                    client, remote_address = s.accept()
                    remote_address = str(remote_address)
                    self._connected_clients[remote_address] = Connection(client, remote_address,
                                                                         self._connected_clients)
                except socket_error:
                    pass

    def stop(self):
        """This method stops the server and disconnects all clients.
        
        It may block until the operating system released all resources.
        """
        self._stopped = True
        self._server_socket.close()
        to_be_stopped = []
        for k_addr in self._connected_clients.keys():
            to_be_stopped.append(self._connected_clients[k_addr])
        for c in to_be_stopped:
            c.stop()
        self._server_thread.join()
