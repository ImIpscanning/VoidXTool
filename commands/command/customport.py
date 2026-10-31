from typing import Optional
from rich.console import Console
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg
from voidxtool.utilities.customport import CustomPortsUtils

console: Console = Console()

class CustomPortCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="customport")
        self.subcommand = None

    def custom_validate_arguments(self, user_arguments):
        '''
Custom validation method to validate the customport command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.subcommand = user_arguments[0]
        if not Validator.is_valid_customport_option(option=self.subcommand):
            console.print(Msg.get(f"commands.{self.name}.messages.invalidOption"))
            return False
        return True

    def run(self, arguments, authentication):
        '''
Run the seeker command.

:param list arguments: The arguments to run the command
:param Authentication authentication: Auth object
:return bool: True if the command was executed successfully, False otherwise
'''
        if not self.validate_arguments(arguments):
            return False

        if self.subcommand == 'add':
            CustomPortsUtils.add_customport()
        elif self.subcommand == 'remove':
            CustomPortsUtils.remove_customport()
        elif self.subcommand == 'list':
            CustomPortsUtils.list_customports()
            
        return True