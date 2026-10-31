"""Local wordlist verification for owner-supplied password hashes."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from rich.console import Console
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()
DEFAULT_WORDLIST = Path(__file__).with_name("wordlist.txt")
WORDLIST = Path(os.getenv("VOIDXTOOL_WORDLIST", str(DEFAULT_WORDLIST))).expanduser()
MAX_HASHES = 10_000


def _matches(candidate: str, encoded: str, salt: str = "") -> bool:
    encoded = encoded.strip()
    if encoded.startswith("SHA256$"):
        parts = encoded.split("$", 2)
        if len(parts) != 3:
            return False
        inner = hashlib.sha256(candidate.encode()).hexdigest()
        return hashlib.sha256((inner + parts[1]).encode()).hexdigest() == parts[2].lower()
    if encoded.startswith("SHA512$"):
        parts = encoded.split("$", 2)
        if len(parts) != 3:
            return False
        inner = hashlib.sha512(candidate.encode()).hexdigest()
        return hashlib.sha512((inner + parts[1]).encode()).hexdigest() == parts[2].lower()
    if len(encoded) == 64:
        return hashlib.sha256(candidate.encode()).hexdigest() == encoded.lower()
    if len(encoded) == 128:
        inner = hashlib.sha512(candidate.encode()).hexdigest()
        return hashlib.sha512((inner + salt).encode()).hexdigest() == encoded.lower()
    return False


def verify_hash(encoded: str, salt: str = "", wordlist: Path = WORDLIST) -> str | None:
    with wordlist.open("r", encoding="latin-1") as handle:
        for line in handle:
            candidate = line.rstrip("\r\n")
            if _matches(candidate, encoded, salt):
                return candidate
    return None


class DeashCommand(BaseCommand):
    def __init__(self) -> None:
        super().__init__("deash")
        self.mode = ""
        self.value = ""

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.mode = str(user_arguments[0]).lower()
        self.value = str(user_arguments[1])
        if self.mode not in {"single", "multiple"}:
            console.print("[red]Mode must be single or multiple.[/red]")
            return False
        if self.mode == "multiple" and not Path(self.value).is_file():
            console.print("[red]Hash file does not exist.[/red]")
            return False
        if not WORDLIST.is_file():
            console.print(
                "[red]Wordlist is missing. Set VOIDXTOOL_WORDLIST to an authorized local file.[/red]"
            )
            return False
        return True

    @staticmethod
    def _split(value: str) -> tuple[str, str]:
        if value.startswith(("SHA256$", "SHA512$")):
            return value, ""
        encoded, separator, salt = value.partition("$")
        return encoded, salt if separator else ""

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False

        if self.mode == "single":
            entries = [self.value]
        else:
            entries = [
                line.strip()
                for line in Path(self.value).read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip()
            ][:MAX_HASHES]

        table = Table(title="Local hash verification", header_style="bold bright_cyan")
        table.add_column("Hash", overflow="fold")
        table.add_column("Result", style="bright_magenta")
        for raw in entries:
            encoded, salt = self._split(raw)
            try:
                result = verify_hash(encoded, salt)
            except OSError as exc:
                console.print(f"[red]Could not read wordlist: {exc}[/red]")
                return False
            table.add_row(encoded[:24] + ("…" if len(encoded) > 24 else ""), result or "not found")
        console.print(table)
        return True

