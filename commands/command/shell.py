import os
import subprocess
from typing import Union, Optional
from rich.console import Console
from ezjsonpy import get_config_value
from rstatus.models import JavaServerResponse, BedrockServerResponse
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.commands.validator import Validator
from voidxtool.commands.base import BaseCommand
from voidxtool.utilities.reverseshell.listener import ReverseShellListener

console: Console = Console()

class ShellCommand(BaseCommand):
    def __init__(self):
        super().__init__('shell')
        self.port = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
        Custom validation method to validate the shell command arguments.

        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        '''
        self.port = user_arguments[0]
        if not Validator.is_port(port=self.port):
            console.print(Msg.get('errors.invalidPort'))
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
        Run the shell command.

        :param arguments: list: The arguments to run the command
        :param authentication: Authentication: Auth object
        :return: bool: True if the command was executed successfully, False otherwise
        '''
        if not self.validate_arguments(arguments):
            return False

        ReverseShellListener(port=int(self.port)).run()
        return True