"""Authorization scope enforcement for network-facing commands."""

from __future__ import annotations

import ipaddress
import json
import os
import socket
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


ACKNOWLEDGEMENT = "I own these systems or have explicit permission to test them."


@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    reason: str


class ScopePolicy:
    """Load and enforce a repository-local assessment scope."""

    ACTIVE_COMMANDS = {
        "audit",
        "autoscan",
        "botattack",
        "brutercon",
        "checker",
        "connect",
        "dnsrecords",
        "ddos",
        "fakeproxy",
        "iphistory",
        "ipinfo",
        "kick",
        "kickall",
        "listening",
        "pterodactyl",
        "proxy",
        "protection",
        "php2shell",
        "rcon",
        "scan",
        "sendcmd",
        "server",
        "shodan",
        "subdomains",
    }
    DISRUPTIVE_COMMANDS = {
        "botattack",
        "brutercon",
        "ddos",
        "kick",
        "kickall",
        "pterodactyl",
        "sendcmd",
    }
    DISCOVERY_COMMANDS = {"randomservers", "scrapper", "websearch"}
    LOCAL_LISTENER_COMMANDS = {"mclistener", "reverseproxy", "shell"}
    SENSITIVE_DATA_COMMANDS = {"anydeskgb", "deash", "password"}

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        configured = path or os.getenv("VOIDXTOOL_SCOPE_FILE") or "scope.json"
        self.path = Path(configured).resolve()
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.is_file():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def status(self) -> tuple[str, str]:
        """Return a compact status and Rich color for the terminal dashboard."""
        if not self.path.is_file():
            return "not configured", "yellow"
        if not self.data:
            return "invalid JSON", "red"
        if self.data.get("acknowledgement") != ACKNOWLEDGEMENT:
            return "acknowledgement missing", "red"
        if not self._date_is_valid():
            return "expired", "red"
        targets = self.data.get("authorized_targets", [])
        count = len(targets) if isinstance(targets, list) else 0
        return f"active · {count} target rule(s) · until {self.data.get('expires')}", "green"

    def display_path(self) -> str:
        """Return a concise path when the scope file is inside the workspace."""
        try:
            return str(self.path.relative_to(Path.cwd()))
        except ValueError:
            return str(self.path)

    def check(self, command: str, arguments: list[str]) -> ScopeDecision:
        protected = (
            command in self.ACTIVE_COMMANDS
            or command in self.DISCOVERY_COMMANDS
            or command in self.LOCAL_LISTENER_COMMANDS
            or command in self.SENSITIVE_DATA_COMMANDS
        )
        if not protected:
            return ScopeDecision(True, "passive or local command")
        if not self.data:
            return ScopeDecision(False, f"Missing or invalid scope file: {self.display_path()}")
        if self.data.get("acknowledgement") != ACKNOWLEDGEMENT:
            return ScopeDecision(False, "The scope acknowledgement is missing or does not match.")
        if not self._date_is_valid():
            return ScopeDecision(False, "The authorization scope has expired or has no valid expiry date.")
        if command in self.DISRUPTIVE_COMMANDS and not self.data.get("allow_disruptive_tests", False):
            return ScopeDecision(False, "This command requires allow_disruptive_tests=true.")
        if command in self.DISCOVERY_COMMANDS:
            allowed = bool(self.data.get("allow_public_discovery", False))
            reason = "This command requires allow_public_discovery=true." if not allowed else "authorized"
            return ScopeDecision(allowed, reason)
        if command in self.SENSITIVE_DATA_COMMANDS:
            allowed = bool(self.data.get("allow_sensitive_data_search", False))
            reason = "Sensitive-data search is not authorized." if not allowed else "authorized"
            return ScopeDecision(allowed, reason)
        if command in self.LOCAL_LISTENER_COMMANDS:
            allowed = bool(self.data.get("allow_local_listeners", False))
            return ScopeDecision(allowed, "Local listeners are not authorized." if not allowed else "authorized")
        if not arguments:
            return ScopeDecision(False, "The command has no target to compare with scope.")
        target = arguments[0]
        if Path(target).is_file():
            return self._check_target_file(Path(target))
        return self._check_target(target)

    def _date_is_valid(self) -> bool:
        raw = self.data.get("expires")
        try:
            return date.fromisoformat(str(raw)) >= date.today()
        except ValueError:
            return False

    def _check_target_file(self, path: Path) -> ScopeDecision:
        try:
            targets = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except OSError:
            return ScopeDecision(False, "The target file could not be read.")
        if not targets:
            return ScopeDecision(False, "The target file is empty.")
        for target in targets:
            decision = self._check_target(target)
            if not decision.allowed:
                return ScopeDecision(False, f"{target}: {decision.reason}")
        return ScopeDecision(True, "all file targets are authorized")

    def _check_target(self, target: str) -> ScopeDecision:
        host = self._extract_host(target)
        if not host:
            return ScopeDecision(False, "The target hostname could not be parsed.")
        allowed_targets = self.data.get("authorized_targets", [])
        if not isinstance(allowed_targets, list) or not allowed_targets:
            return ScopeDecision(False, "authorized_targets is empty.")
        if any(self._matches(host, str(rule)) for rule in allowed_targets):
            return ScopeDecision(True, "target is in the authorized scope")
        return ScopeDecision(False, f"{host} is outside authorized_targets.")

    @staticmethod
    def _extract_host(target: str) -> str | None:
        candidate = target.strip()
        if "://" in candidate:
            return urlsplit(candidate).hostname
        if candidate.count(":") == 1:
            host, possible_port = candidate.rsplit(":", 1)
            if possible_port.isdigit():
                return host.strip("[]")
        return candidate.strip("[]") or None

    @staticmethod
    def _matches(host: str, rule: str) -> bool:
        host_l = host.rstrip(".").lower()
        rule_l = rule.strip().rstrip(".").lower()
        if host_l == rule_l:
            return True
        try:
            network = ipaddress.ip_network(rule_l, strict=False)
        except ValueError:
            return False
        try:
            addresses = {ipaddress.ip_address(host_l)}
        except ValueError:
            try:
                addresses = {
                    ipaddress.ip_address(item[4][0])
                    for item in socket.getaddrinfo(host_l, None, type=socket.SOCK_STREAM)
                }
            except socket.gaierror:
                return False
        return bool(addresses) and all(address in network for address in addresses)
