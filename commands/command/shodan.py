"""Shodan vulnerability intelligence command."""

from __future__ import annotations

import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand
from voidxtool.files import VoidXToolPath
from voidxtool.utilities.shodan import ShodanClientError, ShodanVulnerabilityClient
from voidxtool.utilities.shodan.client import save_report

console = Console()

SEVERITY_COLORS = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "cyan",
    "none": "dim",
    "unknown": "white",
}


class ShodanCommand(BaseCommand):
    def __init__(self) -> None:
        super().__init__("shodan")
        self.target = ""
        self.limit = 10

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.target = str(user_arguments[0]).strip()
        if len(user_arguments) > 1:
            try:
                self.limit = int(user_arguments[1])
            except ValueError:
                console.print("[red]Limit must be a number between 1 and 25.[/red]")
                return False
        if not 1 <= self.limit <= 25:
            console.print("[red]Limit must be between 1 and 25.[/red]")
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False

        try:
            report = ShodanVulnerabilityClient(
                os.getenv("SHODAN_API_KEY", ""),
                os.getenv("NVD_API_KEY"),
            ).inspect(self.target, self.limit)
        except ShodanClientError as exc:
            console.print(Panel(str(exc), title="[bold red]SHODAN ERROR[/bold red]", border_style="red"))
            return False

        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="dim")
        summary.add_column(style="white")
        summary.add_row("TARGET", f"{report.queried_target} → {report.resolved_ip}")
        summary.add_row("ORGANIZATION", report.organization or "unknown")
        summary.add_row("COUNTRY", report.country or "unknown")
        summary.add_row("OPERATING SYSTEM", report.operating_system or "unknown")
        summary.add_row("OPEN PORTS", ", ".join(map(str, report.ports)) or "none reported")
        summary.add_row("SHODAN UPDATED", report.last_update or "unknown")
        summary.add_row("CVE COUNT", str(report.total_cves))
        console.print(Panel(
            summary,
            title="[bold bright_magenta]SHODAN HOST INTELLIGENCE[/bold bright_magenta]",
            border_style="bright_cyan",
        ))

        if not report.findings:
            console.print("[green]Shodan did not report CVE identifiers for this host.[/green]")
        for finding in report.findings:
            color = SEVERITY_COLORS.get(finding.severity, "white")
            score = f"{finding.cvss:.1f}" if finding.cvss is not None else "unknown"
            service_text = ", ".join(finding.services) or "host-level finding"
            body = (
                f"[dim]Severity[/dim] [{color}]{finding.severity.upper()}[/{color}]  "
                f"[dim]CVSS[/dim] {score}  [dim]Source[/dim] {finding.source}\n"
                f"[dim]Observed on[/dim] {service_text}\n\n"
                f"{finding.explanation}\n\n"
                f"[bold cyan]Exploit-DB[/bold cyan] [link={finding.exploit_db_url}]{finding.exploit_db_url}[/link]"
            )
            console.print(Panel(body, title=f"[bold]{finding.cve}[/bold]", border_style=color))

        if report.omitted_cves:
            console.print(
                f"[dim]{len(report.omitted_cves)} additional CVE(s) omitted by the detail limit: "
                f"{', '.join(report.omitted_cves)}[/dim]"
            )

        report_path = save_report(
            report,
            os.path.join(VoidXToolPath.get_voidxtool_data_path(), "reports"),
        )
        console.print(f"[green]Report saved:[/green] {report_path}")
        return True
