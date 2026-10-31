from typing import Optional
from rich.console import Console
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.utilities.webhook import WebhookUtils

console: Console = Console()

class WebhookCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="webhook")
        self.subcommand: str = ""

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        if len(user_arguments) < 1:
            console.print(Msg.get("errors.invalidArguments"))
            return False
        self.subcommand = user_arguments[0]
        if not Validator.is_valid_customport_option(str(self.subcommand)):
            console.print(
                Msg.get(f"commands.{self.name}.messages.invalidOption")
            )
            return False
        return True

    def run(self, arguments: list, _: Authentication) -> bool:
        if not self.validate_arguments(arguments):
            return False
        if self.subcommand == "add":
            WebhookUtils.add_webhook()
        elif self.subcommand == "remove":
            WebhookUtils.remove_webhook()
        elif self.subcommand == "list":
            WebhookUtils.list_webhooks()
        return True