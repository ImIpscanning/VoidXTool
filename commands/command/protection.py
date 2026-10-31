"""
Protection analysis command — probes a host for common defences.
Usage: protection <host:port>
Default port: 25565 (Minecraft)
"""

from __future__ import annotations

import re
import socket
import struct
import time

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()

CF_IPV4_URL = "https://www.cloudflare.com/ips-v4"
CF_IPV6_URL = "https://www.cloudflare.com/ips-v6"


# ── helpers ──────────────────────────────────────────────────────────────────
def _ip_in_cidr(ip: str, cidr: str) -> bool:
    """Return True if ip falls inside the given CIDR block."""
    ip_parts    = [int(x) for x in ip.split(".")]
    net, prefix = cidr.split("/")
    net_parts   = [int(x) for x in net.split(".")]
    prefix      = int(prefix)
    ip_int  = sum(b << (24 - 8 * i) for i, b in enumerate(ip_parts))
    net_int = sum(b << (24 - 8 * i) for i, b in enumerate(net_parts))
    mask    = ((1 << 32) - 1) ^ ((1 << (32 - prefix)) - 1)
    return (ip_int & mask) == (net_int & mask)


def _recv_all(sock: socket.socket, timeout: float = 3.0) -> bytes:
    data = b""
    sock.settimeout(timeout)
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    except (socket.timeout, OSError):
        pass
    return data


def _mc_handshake(ip: str, port: int) -> bytes:
    """Send a Minecraft status handshake and return raw response."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(4)
    try:
        s.connect((ip, port))
        host_enc  = ip.encode()
        handshake = (
            b"\x00"
            + b"\x00"
            + struct.pack("!H", len(host_enc)) + host_enc
            + struct.pack("!H", port)
            + b"\x01"
        )
        length_prefix = struct.pack("!B", len(handshake))
        s.sendall(length_prefix + handshake)
        s.sendall(b"\x01\x00")
        return _recv_all(s)
    finally:
        s.close()


# ── individual checks ─────────────────────────────────────────────────────────
def _check_cloudflare(ip: str) -> tuple[str, str]:
    try:
        resp = requests.get(CF_IPV4_URL, timeout=5)
        for cidr in resp.text.splitlines():
            if cidr and _ip_in_cidr(ip, cidr):
                return "⚠  Cloudflare detected", f"CIDR {cidr}"
        return "✔  No Cloudflare", ""
    except Exception as exc:
        return "?  CF check failed", str(exc)


def _check_tcp_proxy(ip: str) -> tuple[str, str]:
    try:
        hostname = socket.gethostbyaddr(ip)[0].lower()
        proxies  = ["tcpshield", "glider", "proxy", "shield", "guard"]
        for kw in proxies:
            if kw in hostname:
                return f"⚠  Proxy hostname: {hostname}", kw
        return "✔  No proxy rDNS", hostname
    except Exception:
        return "✔  No rDNS record", ""


def _check_firewall(ip: str, port: int) -> tuple[str, str]:
    failed = 0
    for _ in range(8):
        try:
            s = socket.create_connection((ip, port), timeout=1.5)
            s.close()
            time.sleep(0.15)
        except OSError:
            failed += 1
    if failed >= 5:
        return f"⚠  Firewall / rate-limit ({failed}/8 failed)", ""
    return f"✔  No firewall ({failed}/8 failed)", ""


def _check_ddos_resistance(ip: str, port: int) -> tuple[str, str]:
    total, success = 20, 0
    for _ in range(total):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((ip, port))
            s.sendall(b"\xfe\x01")
            if s.recv(256):
                success += 1
            s.close()
            time.sleep(0.05)
        except OSError:
            pass
    rate = success / total
    pct  = int(rate * 100)
    if rate > 0.7:
        return f"✘  Vulnerable to floods ({pct}% success)", "HIGH"
    if rate > 0.4:
        return f"⚠  Partially vulnerable ({pct}% success)", "MEDIUM"
    return f"✔  Resists basic floods ({pct}% success)", "LOW"


def _check_plugin_leak(ip: str, port: int) -> tuple[str, str]:
    try:
        raw  = _mc_handshake(ip, port)
        text = raw.decode("utf-8", errors="ignore")
        m    = re.search(r'(?:"modinfo"|"Plugins")\s*:\s*(\{.*?\})', text)
        if m:
            plugins = re.findall(r'"([A-Za-z0-9_\-]+)"', m.group(1))
            if plugins:
                return f"⚠  Plugins leaked: {', '.join(plugins[:8])}", str(len(plugins))
        return "✔  No plugin leakage", ""
    except Exception as exc:
        return "?  Plugin check failed", str(exc)


def _check_forceop(ip: str, port: int) -> tuple[str, str]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((ip, port))
        s.sendall(b"\x00\x00")
        resp = s.recv(1024).decode("utf-8", errors="ignore")
        s.close()
        keywords = ["ForceOP", "Exploit", "Vuln", "rce", "bypass"]
        for kw in keywords:
            if kw.lower() in resp.lower():
                return f"✘  ForceOP / exploit string found: {kw}", kw
        return "✔  No ForceOP patterns", ""
    except Exception:
        return "✔  No response (likely safe)", ""


def _check_version_disclosure(ip: str, port: int) -> tuple[str, str]:
    try:
        raw  = _mc_handshake(ip, port)
        text = raw.decode("utf-8", errors="ignore")
        m    = re.search(r'"version"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"', text)
        if m:
            return f"⚠  Version disclosed: {m.group(1)}", m.group(1)
        return "✔  No version string", ""
    except Exception:
        return "?  Version check failed", ""


# ── command ───────────────────────────────────────────────────────────────────
class ProtectionCommand(BaseCommand):
    """Probe a server for common protections and misconfigurations."""

    def __init__(self) -> None:
        super().__init__("protection")
        self.host = ""
        self.port = 25565

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        target = str(user_arguments[0]).strip()
        if ":" in target:
            parts = target.rsplit(":", 1)
            self.host = parts[0]
            try:
                self.port = int(parts[1])
            except ValueError:
                console.print("[red]Invalid port.[/red]")
                return False
        else:
            self.host = target
            self.port = 25565
        if not 1 <= self.port <= 65535:
            console.print("[red]Port out of range.[/red]")
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

        console.print(
            Panel(
                f"Target: [bold cyan]{self.host}[/bold cyan] → [yellow]{resolved}[/yellow]:{self.port}",
                title="[bold bright_magenta]PROTECTION ANALYSIS[/bold bright_magenta]",
                border_style="bright_cyan",
            )
        )

        checks = [
            ("Cloudflare",          lambda: _check_cloudflare(resolved)),
            ("TCP Proxy / Shield",  lambda: _check_tcp_proxy(resolved)),
            ("Firewall / Rate-Limit",lambda: _check_firewall(resolved, self.port)),
            ("DDoS Resistance",     lambda: _check_ddos_resistance(resolved, self.port)),
            ("Plugin Leakage",      lambda: _check_plugin_leak(resolved, self.port)),
            ("ForceOP / Exploits",  lambda: _check_forceop(resolved, self.port)),
            ("Version Disclosure",  lambda: _check_version_disclosure(resolved, self.port)),
        ]

        tbl = Table(show_header=True, header_style="bold bright_magenta")
        tbl.add_column("Check",    style="cyan",         min_width=22)
        tbl.add_column("Result",   style="bright_white", min_width=44)
        tbl.add_column("Detail",   style="dim",          min_width=20)

        for name, fn in checks:
            result, detail = fn()
            color = "bright_red" if result.startswith("✘") else \
                    "yellow"     if result.startswith("⚠") else \
                    "bright_green"
            tbl.add_row(name, f"[{color}]{result}[/{color}]", detail)

        console.print(tbl)
        return True
