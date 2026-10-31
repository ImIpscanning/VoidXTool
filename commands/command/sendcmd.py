import subprocess
import os
from typing import Optional, Union
from rich.console import Console
from ezjsonpy import get_config_value
from rstatus.models import JavaServerResponse, BedrockServerResponse
from voidxtool.auth import Authentication
from voidxtool.logs import LogsManager
from voidxtool.utilities import AppChecker
from voidxtool.utilities.minecraft import ServerData
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg
from voidxtool.constants import VoidXToolConstants, NodeJSConstants

console: Console = Console()

class SendCMDCommand(BaseCommand):
    def __init__(self):
        super().__init__('sendcmd')
        self.target = None
        self.version = None
        self.username = None
        self.command_file = None
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
Custom validation method to validate the sendcmd command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.target = user_arguments[0]
        self.version = user_arguments[1]
        self.username = user_arguments[2]
        self.command_file = user_arguments[3]

        if not (Validator.is_domain(self.target) or Validator.is_ip_and_port(self.target) or Validator.is_domain_and_port(self.target)):
            console.print(Msg.get('errors.invalidServer'))
            return False

        if not os.path.isfile(self.command_file):
            console.print(Msg.get('errors.commandsFileNotFound'))
            return False

        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
Run the sendcmd command.

:param arguments: list: The arguments to run the command
:param authentication: Authentication: Auth object
:return: bool: True if the command was executed successfully, False otherwise
'''
        if not self.validate_arguments(arguments):
            return False

        if not AppChecker.nodejs_installed():
            console.print(f"\n{VoidXToolConstants.SPACES}{VoidXToolConstants.PREFIX} [bright_white]NodeJS is not installed. Please install it and restart VoidXTool.")
            return False

        self.logs_manager = LogsManager(command_name=self.name)
        self.logs_manager.write(f"Checking server: {self.target}...")
        console.print(Msg.get(f'commands.{self.name}.messages.checkingServer').replace('%server%', self.target))

        server_data = ServerData.get_data(target=self.target, bot=False)
        if not server_data:
            console.print(Msg.get('errors.serverOffline'))
            return False

        if isinstance(server_data, BedrockServerResponse):
            console.print(Msg.get('errors.notJavaServer'))
            return False

        ip = self.target
        port = str(server_data.port)
        if ':' in self.target:
            ip, port = self.target.split(':')

        console.print(Msg.get(f'commands.{self.name}.messages.gettingCommands').replace('%commandsFile%', self.command_file))
        command_file_path = os.path.abspath(self.command_file)
        
        try:
            with open(command_file_path, 'r', encoding='utf-8') as file:
                commands = file.read().splitlines()
        except UnicodeDecodeError:
            console.print(f"\n{VoidXToolConstants.SPACES}{VoidXToolConstants.PREFIX} [bright_white]The commands file is not UTF-8 encoded.")
            return False

        if len(commands) == 0:
            console.print(Msg.get('errors.commandsFileEmpty'))
            return False

        command = (
            f"{NodeJSConstants.BOT_COMMAND} {NodeJSConstants.BOT_FILE_NAME} sendcmd {ip} {port} "
            f"{self.version} {self.username} {VoidXToolConstants.SPACES} {command_file_path} true - - -"
        )

        if get_config_value('debug'):
            print(f"SendCMD command: {command}")

        self.logs_manager.write(f"Sending SendCMD Bot ({command}) to {self.target}...")
        console.print(
            Msg.get(f'commands.{self.name}.messages.sendingCommands')
            .replace('%server%', f"{ip}:{port}")
            .replace('%username%', self.username)
            .replace('%commandsFile%', self.command_file)
            .replace('%commandsCount%', str(len(commands)))
        )

        subprocess.run(command, shell=True)
        return True