"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
TCP transport implementation for RAVA devices built on top of socket.
"""

import socket

from .rava_comm import RAVAComm, COMM_READ_TIMEOUT_S, COMM_WRITE_TIMEOUT_S
from .rava_errors import RAVAConnectError, RAVAClosedError, RAVADisconnectedError

############################
# RAVA COMM TCP
############################


def sock_read_exactly(sock, n_bytes):
    """
    Repeatedly performs reads until the requested number of bytes `n_bytes` has been received.
    """

    data = bytearray()

    while len(data) < n_bytes:
        try:
            chunk = sock.recv(n_bytes - len(data))

        # Handle timeout
        except socket.timeout:
            continue

        # Client disconnected
        if not chunk:
            return b''

        data.extend(chunk)

    return bytes(data)


class RAVACommTcp(RAVAComm):
    """
    TCP communication transport for RAVA devices.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVACommTcp'
        self.name_conn = ''

        # TCP
        self.sock = None
        self.host = None
        self.port = None
        self.connected = False


    def is_open(self):
        """
        Test whether the local TCP socket is open.

        This method only reports the local socket state. It does not detect whether the connection
        has been closed by the remote peer.
        """

        return (self.sock is not None) and (self.sock.fileno() != -1)


    def open(self, host, port):
        """
        Open a TCP connection to a RAVA server at host:port.
        """

        # Open TCP
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))

        except OSError as err:
            self.close()

            raise RAVAConnectError(
                f'{self.name} open -> Could not open {host}:{port} :-('
                ) from err

        self.host = host
        self.port = port

        # Log
        self.log.info(f'{self.name} open -> Connected to {host}:{port} :-)')

        # RAVAComm open
        super().open()

        # Update connection identifier
        self.name_conn = f': SN={self.serial_number} @ {host}:{port}'


    def close(self):
        """
        Close the TCP connection and stop communication.
        """

        if self.sock is None:
            return

        # RAVAComm close
        super().close()

        # Close USB connection
        try:
            self.sock.shutdown(socket.SHUT_RDWR)

        except Exception:
            pass

        self.sock.close()
        self.sock = None

        # Log
        self.log.info(f'{self.name} close {self.name_conn} -> Connection closed')


    def read(self, n_bytes, timeout = COMM_READ_TIMEOUT_S):
        """
        Returns bytes read from the RAVA TCP server.

        In the case n_bytes > 1, the returned byte string may contain fewer bytes than the
        requested. Returns b'' if no data is received before the configured read timeout expires.

        To ensure that exactly n_bytes are read, use sock_read_exactly().
        """

        # Open?
        if not self.is_open():
            raise RAVAClosedError(
                f'{self.name} read {self.name_conn} -> Attempt to read from a closed device'
                )

        # Set timeout
        self.sock.settimeout(timeout)

        # Read
        try:
            recv = self.sock.recv(n_bytes)

        # Handle timeout
        except socket.timeout:
            return b''

        # Close device and propagate error
        except OSError as err:
            self.close()

            raise RAVADisconnectedError(
                f'{self.name} read {self.name_conn} -> Connection error :-('
                ) from err

        # Client disconnected; Close device and propagate error
        if recv == b'':
            self.close()

            raise RAVADisconnectedError(
                f'{self.name} read {self.name_conn} -> Device disconnected by remote peer :-('
                )

        return recv


    def write(self, comm_bytes):
        """
        Write bytes to the RAVA TCP server.
        """

        # Open?
        if not self.is_open():
            raise RAVAClosedError(
                f'{self.name} write {self.name_conn} -> Attempt to write to a closed device'
                )

        # Set timeout
        self.sock.settimeout(COMM_WRITE_TIMEOUT_S)

        # Write
        try:
            self.sock.sendall(comm_bytes)

        # Close device and propagate error
        except OSError as err:
            self.close()

            raise RAVADisconnectedError(
                f'{self.name} write {self.name_conn} -> Device disconnected :-('
                ) from err