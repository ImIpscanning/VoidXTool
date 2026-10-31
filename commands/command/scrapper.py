"""One-shot parser for public recent-purchase panels on known Minecraft stores."""

from __future__ import annotations

from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()
MAX_PAGE_BYTES = 2_000_000
MAX_ENTRIES = 25

SOURCES = {
    "nauticmc": "https://store.nauticmc.net/",
    "hydracraft": "https://tienda.hydracraft.es/",
    "quickland": "https://quickland.tebex.io/",
    "meetionmc": "https://tienda.meetionmc.com/",
    "mineday": "https://tienda.mineday.us/",
    "minefun": "https://tienda.minefun.net/",
    "doomland": "https://doomlanddd.tebex.io/",
    "minebosh": "https://tienda.minebosh.xyz/",
    "prismamc": "https://tienda.prismamc.net/",
    "supercraft": "https://tienda.supercraft.es/",
    "zestian": "https://tienda.zestian.co/",
    "revengenetwork": "https://tienda.revengenetwork.es/",
}


@dataclass(frozen=True)
class StoreEntry:
    buyer: str
    product: str


def parse_store_entries(content: bytes) -> list[StoreEntry]:
    soup = BeautifulSoup(content, "html.parser")
    selectors = [
        "div.payment-pr",
        "li.payment",
        "div.purchase-item",
        "div.recent-payment",
        "div.widget-module__payment",
    ]
    nodes = []
    for selector in selectors:
        nodes.extend(soup.select(selector))

    entries: list[StoreEntry] = []
    seen: set[tuple[str, str]] = set()
    for node in nodes:
        buyer_node = node.select_one("h5, .user, .username, p")
        product_node = node.select_one(".payment-item, .product, .item, p + p")
        buyer = buyer_node.get_text(" ", strip=True) if buyer_node else "unknown"
        product = product_node.get_text(" ", strip=True) if product_node else "not published"
        key = (buyer, product)
        if key in seen:
            continue
        seen.add(key)
        entries.append(StoreEntry(buyer[:80], product[:120]))
        if len(entries) >= MAX_ENTRIES:
            break
    return entries


class ScrapperCommand(BaseCommand):
    def __init__(self, session: requests.Session | None = None) -> None:
        super().__init__("scrapper")
        self.source = ""
        self.session = session or requests.Session()

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.source = str(user_arguments[0]).lower()
        if self.source not in SOURCES:
            console.print(f"[red]Unknown source. Available: {', '.join(sorted(SOURCES))}[/red]")
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False
        url = SOURCES[self.source]
        try:
            response = self.session.get(url, timeout=10, headers={"User-Agent": "VoidXTool/3.2"})
            response.raise_for_status()
        except requests.RequestException as exc:
            console.print(f"[red]Store request failed: {exc}[/red]")
            return False
        if len(response.content) > MAX_PAGE_BYTES:
            console.print("[red]Store response exceeded the 2 MB safety limit.[/red]")
            return False

        entries = parse_store_entries(response.content)
        if not entries:
            console.print("[yellow]No public recent-purchase entries matched the supported layouts.[/yellow]")
            return True

        table = Table(title=f"Public recent purchases · {self.source}", header_style="bold bright_cyan")
        table.add_column("Public username")
        table.add_column("Product")
        for entry in entries:
            table.add_row(entry.buyer, entry.product)
        console.print(table)
        return True

