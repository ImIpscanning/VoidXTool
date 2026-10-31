from typing import Optional
from rich.console import Console
from voidxtool.auth import Authentication
from voidxtool.logs import LogsManager
from voidxtool.utilities.mcserverscanner.manager import MCServerScanner
from voidxtool.utilities.velocity import StartProxy
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg

console: Console = Console()

class RandomServers(BaseCommand):
    def __init__(self):
        super().__init__('randomservers')
        self.target = None
        self.logs_manager = None
        self.minimum = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
Custom validation method to validate the server command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.minimum = user_arguments[0]
        if not Validator.is_valid_randomservers_minimum(minimum=self.minimum):
            console.print(Msg.get('errors.invalidRandomServersAmount'))
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
Run the randomservers command.

:param list arguments: The arguments to run the command
:param Authentication authentication: Auth object
:return bool: True if the command was executed successfully, False otherwise
'''
        if not self.validate_arguments(arguments):
            return False

        self.logs_manager = LogsManager(command_name=self.name)
        MCServerScanner(
            min_servers=int(self.minimum),
            command_name=self.name,
            logs_manager=self.logs_manager
        ).get_servers()
        return True