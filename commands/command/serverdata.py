from typing import Optional
from rich.console import Console
from ezjsonpy import set_config_value
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg

console: Console = Console()

class ServerDataCommand(BaseCommand):
    def __init__(self):
        super().__init__('serverdata')
        self.mode = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
        Custom validation method to validate the serverdata command arguments.

        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        '''
        self.mode = str(user_arguments[0])
        if not Validator.is_valid_serverdata_mode(mode=self.mode):
            console.print(Msg.get(f'commands.{self.name}.messages.invalidMode'))
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
        Run the serverdata command.

        :param arguments: list: The arguments to run the command
        :param authentication: Authentication: Auth object
        :return: bool: True if the command was executed successfully, False otherwise
        '''
        if not self.validate_arguments(arguments):
            return False

        set_config_value(key='serverStatusGetMode', value=self.mode)
        console.print(Msg.get(f'commands.{self.name}.messages.success'))
        return True