"""Authorized, low-impact Minecraft status audit command."""

from rich.console import Console
from rich.table import Table

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand
from voidxtool.files import VoidXToolPath
from voidxtool.utilities.minecraft.audit import audit_server, save_report

console = Console()


class AuditCommand(BaseCommand):
    def __init__(self) -> None:
        super().__init__("audit")
        self.target = ""
        self.edition = "java"

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.target = str(user_arguments[0])
        self.edition = str(user_arguments[1]).lower() if len(user_arguments) > 1 else "java"
        if self.edition not in {"java", "bedrock"}:
            console.print("[red]Edition must be java or bedrock.[/red]")
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False
        report = audit_server(self.target, self.edition)
        path = save_report(report, f"{VoidXToolPath.get_voidxtool_data_path()}/reports")

        table = Table(title=f"Minecraft {self.edition.capitalize()} audit")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Target", f"{report.target}:{report.port}")
        table.add_row("Online", "yes" if report.online else "no")
        table.add_row("Latency", f"{report.latency_ms} ms" if report.latency_ms is not None else "-")
        if report.error:
            table.add_row("Error", report.error)
        for finding in report.findings:
            table.add_row(f"[{finding.severity}] {finding.title}", finding.evidence)
        table.add_row("Report", str(path))
        console.print(table)
        return True
