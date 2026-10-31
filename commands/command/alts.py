"""Public Minecraft profile and username-history lookup."""

from __future__ import annotations

import re

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")


class AltsCommand(BaseCommand):
    def __init__(self, session: requests.Session | None = None) -> None:
        super().__init__("alts")
        self.username = ""
        self.session = session or requests.Session()

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.username = str(user_arguments[0]).strip()
        if not USERNAME_RE.fullmatch(self.username):
            console.print("[red]Minecraft username must contain 3–16 letters, numbers, or underscores.[/red]")
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False

        try:
            profile_response = self.session.get(
                f"https://api.mojang.com/users/profiles/minecraft/{self.username}",
                timeout=8,
                headers={"User-Agent": "VoidXTool/3.2"},
            )
        except requests.RequestException as exc:
            console.print(f"[red]Mojang profile lookup failed: {exc}[/red]")
            return False

        if profile_response.status_code in {204, 404}:
            console.print(Panel(
                "No public Java profile was returned. No private databases were queried.",
                title=f"[bold]{self.username}[/bold]",
                border_style="yellow",
            ))
            return True
        if profile_response.status_code != 200:
            console.print(f"[red]Mojang returned HTTP {profile_response.status_code}.[/red]")
            return False

        try:
            profile = profile_response.json()
            player_id = str(profile["id"])
            canonical_name = str(profile.get("name", self.username))
        except (ValueError, KeyError, TypeError):
            console.print("[red]Mojang returned an invalid profile response.[/red]")
            return False

        history: list[dict] = []
        try:
            history_response = self.session.get(
                f"https://laby.net/api/v2/user/{player_id}/get-profile",
                timeout=8,
                headers={"User-Agent": "VoidXTool/3.2"},
            )
            if history_response.status_code == 200:
                payload = history_response.json()
                if isinstance(payload, dict) and isinstance(payload.get("username_history"), list):
                    history = payload["username_history"][:50]
        except (requests.RequestException, ValueError):
            history = []

        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="dim")
        summary.add_column(style="white")
        summary.add_row("CURRENT NAME", canonical_name)
        summary.add_row("UUID", player_id)
        summary.add_row("PROFILE", "public Java account")
        console.print(Panel(summary, title="[bold bright_magenta]MINECRAFT PROFILE[/bold bright_magenta]"))

        if history:
            table = Table(title="Public username history", header_style="bold bright_cyan")
            table.add_column("Username")
            table.add_column("Changed at", style="dim")
            for entry in history:
                if not isinstance(entry, dict):
                    continue
                table.add_row(str(entry.get("username", "unknown")), str(entry.get("changed_at") or "unknown"))
            console.print(table)
        else:
            console.print("[dim]No public username history was returned by the profile provider.[/dim]")
        return True

