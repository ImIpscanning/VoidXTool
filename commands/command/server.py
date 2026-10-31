from typing import Union, Optional
from rich.console import Console
from rstatus.models import JavaServerResponse, BedrockServerResponse
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.commands.validator import Validator
from voidxtool.commands.base import BaseCommand
from voidxtool.utilities.minecraft.server_data import ServerData
from voidxtool.utilities.minecraft.show_server import ShowMinecraftServer
from voidxtool.logs import LogsManager

console: Console = Console()

class ServerCommand(BaseCommand):
    def __init__(self):
        super().__init__('server')
        self.target = ''
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
        Custom validation method to validate the server command arguments.

        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        '''
        self.target = user_arguments[0]
        if not (Validator.is_domain(self.target) or Validator.is_ip_and_port(self.target) or Validator.is_domain_and_port(self.target)):
            console.print(Msg.get('errors.invalidServer'))
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
        Run the server command.

        :param arguments: list: The arguments to run the command
        :param authentication: Authentication: Auth object
        :return: bool: True if the command was executed successfully, False otherwise
        '''
        if not self.validate_arguments(arguments):
            return False

        self.logs_manager = LogsManager(command_name=self.name)
        self.logs_manager.write(f"Getting server data for the server: {self.target}")
        console.print(
            Msg.get(f'commands.{self.name}.messages.gettingServerData').replace('%server%', self.target)
        )

        server_data = ServerData.get_data(target=self.target, server_command=True)
        if not server_data:
            self.logs_manager.write(f"The server {self.target} is offline")
            console.print(Msg.get('errors.serverOffline'))
            return False

        ShowMinecraftServer().show(server_data=server_data, server_command=True)
        ShowMinecraftServer().save_to_log(server_data=server_data, logs_manager=self.logs_manager)
        return True