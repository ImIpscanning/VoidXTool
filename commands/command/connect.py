import subprocess
import os
from typing import Optional, Union
from rich.console import Console
from ezjsonpy import get_config_value
from rstatus.models import JavaServerResponse, BedrockServerResponse
from voidxtool.logs import LogsManager
from voidxtool.utilities.minecraft import ServerData
from voidxtool.utilities.app_checker import AppChecker
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg
from voidxtool.constants import VoidXToolConstants, NodeJSConstants

console: Console = Console()

class ConnectCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="connect")
        self.target = None
        self.version = None
        self.username = None
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments):
        '''
Custom validation method to validate the server command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.target = str(user_arguments[0])
        self.version = user_arguments[1]
        self.username = user_arguments[2]
        if not (Validator.is_domain(domain=self.target) or 
                Validator.is_ip_and_port(ip=self.target) or 
                Validator.is_domain_and_port(domain=self.target)):
            console.print(Msg.get('errors.invalidServer'))
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

        if not AppChecker.nodejs_installed():
            console.print(f"\n{VoidXToolConstants.SPACES}{VoidXToolConstants.PREFIX} [bright_white]NodeJS is not installed. Please install it and restart VoidXTool.")
            return False

        self.logs_manager = LogsManager(command_name=self.name)
        console.print(Msg.get(f"commands.{self.name}.messages.checkingServer").replace("%server%", self.target))

        server_data = ServerData(self.target, bot=False).get_data()
        if not server_data:
            console.print(Msg.get('errors.serverOffline'))
            return False

        if isinstance(server_data, BedrockServerResponse):
            console.print(Msg.get('errors.notJavaServer'))
            return False

        if ":" in self.target:
            ip, port = self.target.split(":")
        else:
            ip = self.target
            port = str(server_data.port)

        command = f"{NodeJSConstants.BOT_COMMAND} {NodeJSConstants.CONNECT_FILE_NAME} {ip} {port} {self.version} {self.username} false -"
        if os.name == "nt":
            command = f"C: && {command}"

        if get_config_value("debug"):
            print(f"Connect command: {command}")

        console.print(Msg.get(f"commands.{self.name}.messages.connecting").replace("%server%", f"{ip}:{port}").replace("%username%", self.username))
        self.logs_manager.write(f"Sending bot command: {command}...")
        subprocess.run(command, shell=True)
        return True