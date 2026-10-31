"""Inspect local AnyDesk process connections with bounded waiting."""

from __future__ import annotations

import ipaddress
import platform
import time

import psutil
import requests
from rich.console import Console
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()


def _anydesk_endpoints() -> set[tuple[str, int, int]]:
    endpoints: set[tuple[str, int, int]] = set()
    for process in psutil.process_iter(["pid", "name"]):
        try:
            name = str(process.info.get("name") or "").lower()
            if "anydesk" not in name:
                continue
            for connection in process.net_connections(kind="tcp"):
                if not connection.raddr:
                    continue
                remote_ip = getattr(connection.raddr, "ip", connection.raddr[0])
                remote_port = getattr(connection.raddr, "port", connection.raddr[1])
                endpoints.add((str(remote_ip), int(remote_port), int(process.pid)))
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            continue
    return endpoints


class AnyDeskGBCommand(BaseCommand):
    def __init__(self) -> None:
        super().__init__("anydeskgb")
        self.wait_seconds = 10

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        if user_arguments:
            try:
                self.wait_seconds = int(user_arguments[0])
            except ValueError:
                console.print("[red]Wait time must be an integer from 0 to 120.[/red]")
                return False
        if not 0 <= self.wait_seconds <= 120:
            console.print("[red]Wait time must be between 0 and 120 seconds.[/red]")
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False
        if platform.system() != "Windows":
            console.print("[yellow]AnyDesk local inspection is available on Windows only.[/yellow]")
            return False

        deadline = time.monotonic() + self.wait_seconds
        endpoints: set[tuple[str, int, int]] = set()
        try:
            while True:
                endpoints = _anydesk_endpoints()
                if endpoints or time.monotonic() >= deadline:
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("[yellow]AnyDesk inspection cancelled.[/yellow]")
            return False

        if not endpoints:
            console.print("[yellow]No active AnyDesk remote endpoints were found.[/yellow]")
            return True

        table = Table(title="Local AnyDesk remote endpoints", header_style="bold bright_cyan")
        table.add_column("PID")
        table.add_column("Remote endpoint")
        table.add_column("Network owner/location")
        for remote_ip, remote_port, pid in sorted(endpoints)[:20]:
            details = "local/private address"
            try:
                if ipaddress.ip_address(remote_ip).is_global:
                    response = requests.get(f"https://ipinfo.io/{remote_ip}/json", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        details = ", ".join(filter(None, [data.get("org"), data.get("city"), data.get("country")]))
                        details = details or "public address"
            except (ValueError, requests.RequestException):
                details = "metadata unavailable"
            table.add_row(str(pid), f"{remote_ip}:{remote_port}", details)
        console.print(table)
        console.print("[dim]Endpoints may be AnyDesk relay infrastructure; they are not identified as the peer device.[/dim]")
        return True

