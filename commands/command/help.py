"""Categorized command reference for the terminal console."""

from __future__ import annotations

from ezjsonpy import translate_message
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()

DESCRIPTIONS = {
    "audit": "Low-impact Java or Bedrock status assessment and JSON report.",
    "shodan": "Read host CVEs and pivot to Exploit-DB; optional detail limit: 1–25.",
    "alts": "Read a public Minecraft profile and published username history.",
    "anydeskgb": "Inspect local AnyDesk remote endpoints with bounded waiting.",
    "ddos": "Run a strictly bounded, low-volume UDP availability test.",
    "deash": "Verify owner-supplied hashes against a configured local wordlist.",
    "scrapper": "Read one public recent-purchase page from a known Minecraft store.",
    "protection": "Run bounded checks for common server protections and disclosures.",
    "reverseproxy": "Open a local TCP listener when listeners are authorized.",
    "php2shell": "Check PHP2Shell CVE exposure without running the exploit chain.",
    "server": "Read status metadata from an authorized Minecraft server.",
    "uuid": "Resolve an online or offline player UUID.",
    "ipinfo": "Show network ownership and location metadata for an authorized IP.",
    "iphistory": "Review historical DNS data for an authorized domain.",
    "dnsrecords": "Read DNS records for an authorized domain.",
    "checker": "Validate server targets supplied in a scoped file.",
    "subdomains": "Check a scoped wordlist against an authorized domain.",
    "websearch": "Discover public server listings when discovery is authorized.",
    "scan": "Run a configured scanner against an authorized target.",
    "autoscan": "Run scheduled scans against an authorized target file.",
    "listening": "Monitor an authorized endpoint for Minecraft traffic.",
    "proxy": "Start a Velocity proxy for an authorized test server.",
    "fakeproxy": "Start the legacy proxy compatibility workflow.",
    "connect": "Connect one test client to an authorized server.",
    "sendcmd": "Run a command-file workflow in an approved disruptive test.",
    "kick": "Exercise one approved disconnect test.",
    "kickall": "Exercise an approved multi-client disconnect test.",
    "botattack": "Run the preserved load-test workflow when explicitly authorized.",
    "rcon": "Open RCON with credentials supplied by the server owner.",
    "brutercon": "Run the preserved credential test with disruptive approval.",
    "shell": "Start a local listener when listeners are explicitly authorized.",
    "mclistener": "Start the Minecraft listener workflow.",
    "customport": "Manage additional Minecraft service ports.",
    "password": "Use the preserved sensitive-data lookup when explicitly approved.",
    "webhook": "Manage local report webhook configuration.",
    "vulnserver": "Launch a deliberately vulnerable local lab server.",
    "pterodactyl": "Run the preserved panel assessment workflow in approved scope.",
    "clearservers": "Clear locally saved server results.",
    "language": "Change the terminal language.",
    "settings": "Open or reload local settings.",
    "history": "Show recent local commands.",
    "debug": "Toggle detailed diagnostic output.",
    "serverdata": "Choose the local or external status provider.",
    "randomservers": "Use preserved public discovery with explicit approval.",
    "clear": "Clear and redraw the console.",
}

CATEGORIES = {
    "Assessment": [
        "audit", "shodan", "php2shell", "protection", "server", "checker", "scan",
        "autoscan", "rcon", "dnsrecords", "subdomains",
    ],
    "Identity & intelligence": [
        "uuid", "alts", "ipinfo", "iphistory", "websearch", "scrapper",
        "randomservers", "password", "deash", "anydeskgb",
    ],
    "Lab & advanced": [
        "connect", "sendcmd", "kick", "kickall", "botattack", "brutercon", "ddos",
        "pterodactyl", "proxy", "fakeproxy", "listening", "mclistener",
        "shell", "reverseproxy", "vulnserver",
    ],
    "Workspace": [
        "customport", "webhook", "clearservers", "language", "settings",
        "history", "debug", "serverdata", "clear",
    ],
}

DISRUPTIVE = {"sendcmd", "kick", "kickall", "botattack", "brutercon", "ddos", "pterodactyl"}
SCOPED = {
    "audit", "shodan", "server", "checker", "scan", "autoscan", "rcon", "dnsrecords",
    "subdomains", "ipinfo", "iphistory", "connect", "proxy", "fakeproxy",
    "listening", "websearch", "scrapper", "randomservers", "password", "deash",
    "anydeskgb", "ddos", "php2shell", "protection", "mclistener", "reverseproxy", "shell",
}


class HelpCommand(BaseCommand):
    def __init__(self) -> None:
        super().__init__(name="help")

    def run(self, arguments, authentication: Authentication) -> bool:
        del arguments, authentication
        for category, names in CATEGORIES.items():
            table = Table(show_header=True, header_style="bold bright_cyan", expand=True, padding=(0, 1))
            table.add_column("Command", style="bold bright_magenta", width=13, no_wrap=True)
            table.add_column("Usage", style="cyan", width=23)
            table.add_column("Description", style="white", ratio=1)
            for name in names:
                raw_args = translate_message(f"commands.{name}.args") or []
                args_text = " ".join(str(item) for item in raw_args)
                if name in DISRUPTIVE:
                    command_text = f"[red]! {name}[/red]"
                elif name in SCOPED:
                    command_text = f"[cyan]› {name}[/cyan]"
                else:
                    command_text = name
                table.add_row(command_text, args_text or "—", DESCRIPTIONS[name])
            console.print(Panel(table, title=f"[bold]{category}[/bold]", border_style="bright_magenta"))

        console.print(
            "[cyan]›[/cyan] scoped target · [red]![/red] disruptive approval · "
            "[dim]Console:[/dim] [cyan]dashboard[/cyan] · [cyan]scope[/cyan] · "
            "[cyan]about[/cyan] · [cyan]exit[/cyan]"
        )
        return True
