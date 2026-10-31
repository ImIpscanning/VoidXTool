"""Non-destructive PHP2Shell exposure check for authorized web servers."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()

FIXED_RELEASES = {
    (8, 2): (8, 2, 35),
    (8, 3): (8, 3, 36),
    (8, 4): (8, 4, 27),
    (8, 5): (8, 5, 12),
}

CVES = {
    "CVE-2026-109618": "Out-of-memory cleanup can consume partially initialized request data.",
    "CVE-2026-109619": "Request-owned global state can survive after its memory is released.",
}


def classify_php_version(version: tuple[int, int, int]) -> tuple[str, str]:
    fixed = FIXED_RELEASES.get(version[:2])
    if fixed is None:
        return "unknown", "This PHP branch is outside the supported comparison table."
    if version < fixed:
        return "potentially exposed", f"Update to PHP {'.'.join(map(str, fixed))} or newer."
    return "patched", f"This version meets the fixed release for PHP {version[0]}.{version[1]}."


class PHP2ShellCommand(BaseCommand):
    def __init__(self, session: requests.Session | None = None) -> None:
        super().__init__("php2shell")
        self.session = session or requests.Session()
        self.host = ""
        self.port = 80
        self.path = "/index.php"
        self.scheme = "http"

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        raw_target = str(user_arguments[0]).strip()
        parsed = urlsplit(raw_target if "://" in raw_target else f"//{raw_target}")
        self.host = parsed.hostname or ""
        if not self.host:
            console.print("[red]A valid hostname or IP is required.[/red]")
            return False
        try:
            embedded_port = parsed.port
            self.port = int(user_arguments[1]) if len(user_arguments) > 1 else (embedded_port or 80)
        except ValueError:
            console.print("[red]Port must be a number from 1 to 65535.[/red]")
            return False
        if not 1 <= self.port <= 65535:
            console.print("[red]Port must be between 1 and 65535.[/red]")
            return False
        self.scheme = parsed.scheme or ("https" if self.port == 443 else "http")
        if self.scheme not in {"http", "https"}:
            console.print("[red]Only HTTP and HTTPS targets are supported.[/red]")
            return False
        self.path = str(user_arguments[2]) if len(user_arguments) > 2 else (parsed.path or "/index.php")
        if not self.path.startswith("/"):
            self.path = "/" + self.path
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False

        display_host = f"[{self.host}]" if ":" in self.host else self.host
        url = f"{self.scheme}://{display_host}:{self.port}{self.path}"
        try:
            response = self.session.get(
                url,
                timeout=8,
                allow_redirects=False,
                stream=True,
                headers={"User-Agent": "VoidXTool/3.2 PHP exposure check"},
            )
            response.close()
        except requests.RequestException as exc:
            console.print(f"[red]PHP exposure check failed: {exc}[/red]")
            return False

        powered_by = response.headers.get("X-Powered-By", "")
        server = response.headers.get("Server", "")
        match = re.search(r"PHP/(\d+)\.(\d+)\.(\d+)", f"{powered_by} {server}", re.IGNORECASE)

        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="dim")
        summary.add_column(style="white")
        summary.add_row("TARGET", url)
        summary.add_row("HTTP STATUS", str(response.status_code))
        summary.add_row("SERVER", server or "not disclosed")

        if match:
            version = tuple(int(part) for part in match.groups())
            status, guidance = classify_php_version(version)
            color = "red" if status == "potentially exposed" else "green" if status == "patched" else "yellow"
            summary.add_row("PHP VERSION", ".".join(map(str, version)))
            summary.add_row("ASSESSMENT", f"[{color}]{status.upper()}[/{color}]")
            summary.add_row("GUIDANCE", guidance)
        else:
            summary.add_row("PHP VERSION", "not disclosed")
            summary.add_row("ASSESSMENT", "[yellow]INCONCLUSIVE[/yellow]")
            summary.add_row("GUIDANCE", "Confirm the installed PHP package locally or with authenticated inventory.")

        console.print(Panel(
            summary,
            title="[bold bright_magenta]PHP2SHELL EXPOSURE CHECK[/bold bright_magenta]",
            border_style="bright_cyan",
        ))
        for cve, explanation in CVES.items():
            exploit_db = f"https://www.exploit-db.com/search?cve={cve}"
            console.print(f"[bold]{cve}[/bold] · {explanation}\n[link={exploit_db}]{exploit_db}[/link]")
        console.print("[dim]This command sends one normal HTTP request and does not execute the exploit chain.[/dim]")
        return True

