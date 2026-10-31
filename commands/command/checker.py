import os
import re
from typing import Optional
from rich.console import Console
from voidxtool.gui.language import Msg
from voidxtool.commands.base import BaseCommand
from voidxtool.utilities.minecraft.get_servers import GetServersData, ServersFound
from voidxtool.logs import LogsManager
from voidxtool.auth.login import Authentication

console: Console = Console()

class CheckerCommand(BaseCommand):
    def __init__(self):
        super().__init__(name='checker')
        self.file = ''
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.file = user_arguments[0]
        if not os.path.exists(self.file):
            console.print(Msg.get('errors.invalidFile'))
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        if not self.validate_arguments(arguments):
            return False
        self.custom_validate_arguments(arguments)
        self.logs_manager = LogsManager()
        servers = GetServersData.load(self.file)
        found = ServersFound.find(servers)
        console.print(f"Servers found: {len(found)}")
        return True