"""
Reverse proxy / shell listener command.
Usage: reverseproxy <port> [--tcp | --shell]
  --tcp   raw TCP listener (default)
  --shell interactive shell relay via ncat
"""

from __future__ import annotations

import subprocess
import socket
import threading
import sys
import os

from rich.console import Console
from rich.panel import Panel

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()


# ── raw TCP listener (no external deps) ──────────────────────────────────────
def _tcp_listener(port: int) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind(("0.0.0.0", port))
        srv.listen(1)
        console.print(f"[green][+][/green] Listening on 0.0.0.0:{port} — waiting for connection…")
        conn, addr = srv.accept()
        console.print(f"[bright_green][+] Connection from {addr[0]}:{addr[1]}[/bright_green]")
        conn.settimeout(None)

        def _recv() -> None:
            try:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
            except OSError:
                pass

        t = threading.Thread(target=_recv, daemon=True)
        t.start()

        try:
            for line in sys.stdin:
                conn.sendall(line.encode())
        except (KeyboardInterrupt, OSError):
            pass
        finally:
            conn.close()
    finally:
        srv.close()


# ── ncat shell relay ──────────────────────────────────────────────────────────
def _ncat_listener(port: int) -> None:
    console.print(f"[green][+][/green] Starting ncat shell relay on port {port}…")
    try:
        proc = subprocess.Popen(
            ["ncat", "-lvp", str(port)],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        proc.wait()
    except FileNotFoundError:
        console.print(
            "[red][!] ncat not found — falling back to raw TCP listener.[/red]"
        )
        _tcp_listener(port)
    except KeyboardInterrupt:
        pass


# ── command ───────────────────────────────────────────────────────────────────
class ReverseProxyCommand(BaseCommand):
    """Listen for an incoming reverse shell / TCP connection."""

    def __init__(self) -> None:
        super().__init__("reverseproxy")
        self.port  = 0
        self.mode  = "tcp"

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        try:
            self.port = int(user_arguments[0])
        except (ValueError, IndexError):
            console.print("[red]Usage: reverseproxy <port> [--tcp | --shell][/red]")
            return False

        if not 1 <= self.port <= 65535:
            console.print("[red]Port out of range (1–65535).[/red]")
            return False

        self.mode = "shell" if len(user_arguments) > 1 and "--shell" in user_arguments else "tcp"
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False

        console.print(
            Panel(
                f"Port: [bold cyan]{self.port}[/bold cyan]   "
                f"Mode: [bold yellow]{self.mode.upper()}[/bold yellow]\n"
                f"[dim]Ctrl+C to stop[/dim]",
                title="[bold bright_magenta]REVERSE PROXY LISTENER[/bold bright_magenta]",
                border_style="bright_cyan",
            )
        )

        try:
            if self.mode == "shell":
                _ncat_listener(self.port)
            else:
                _tcp_listener(self.port)
        except KeyboardInterrupt:
            console.print("\n[yellow][!] Listener stopped.[/yellow]")

        return True
