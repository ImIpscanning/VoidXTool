import os
import socket
import ssl
import select
import struct
import time
from typing import Optional

if os.name != 'nt':
    import signal

class MCRconException(Exception):
    """Exception class for MCRcon"""
    pass

def timeout_handler(signum, frame):
    """Signal handler for the timeout"""
    raise MCRconException("Connection timeout error")

class MCRcon:
    rcon_socket: Optional[socket.socket] = None

    def __init__(self, host: str, password: Optional[str], port: int = 25575, tlsmode: int = 0, timeout: int = 5):
        self.host = host
        self.password = password
        self.port = port
        self.tlsmode = tlsmode
        self.timeout = timeout
        if os.name != 'nt':
            signal.signal(signal.SIGALRM, timeout_handler)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.disconnect()

    def connect(self):
        self.rcon_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.tlsmode > 0:
            context = ssl.create_default_context()
            if self.tlsmode > 1:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            self.rcon_socket = context.wrap_socket(self.rcon_socket, server_hostname=self.host)
        self.rcon_socket.connect((self.host, self.port))
        if self.password:
            self._send(3, self.password)

    def disconnect(self):
        if self.rcon_socket:
            self.rcon_socket.close()
            self.rcon_socket = None

    def _read(self, length: int) -> bytes:
        if os.name != 'nt':
            signal.alarm(self.timeout)
        data = b''
        while len(data) < length:
            chunk = self.rcon_socket.recv(length - len(data))
            if not chunk:
                raise MCRconException("Connection closed by remote host")
            data += chunk
        if os.name != 'nt':
            signal.alarm(0)
        return data

    def _send(self, out_type: int, out_data: str) -> str:
        out_id = 0xBADC0DE
        payload = out_data.encode('utf-8')
        packet = struct.pack('<iii', len(payload) + 10, out_id, out_type) + payload + b'\x00\x00'
        self.rcon_socket.sendall(packet)
        resp_len_bytes = self._read(4)
        resp_len = struct.unpack('<i', resp_len_bytes)[0]
        resp_data = self._read(resp_len)
        if len(resp_data) < 8:
            raise MCRconException("Invalid response from server")
        resp_id, resp_type = struct.unpack('<ii', resp_data[:8])
        body = resp_data[8:-2].decode('utf-8', errors='ignore')
        return body

    def command(self, command: str) -> str:
        result = self._send(2, command)
        time.sleep(0.003)
        return result

    def is_rcon_enabled(self) -> bool:
        try:
            self.connect()
            self._send(3, 'invalid_password5')
            resp_len_bytes = self._read(4)
            resp_len = struct.unpack('<i', resp_len_bytes)[0]
            resp_data = self._read(resp_len)
            return True
        except Exception:
            return False
        finally:
            self.disconnect()