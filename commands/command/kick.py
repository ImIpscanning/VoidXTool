from typing import Optional, Union
from rich.console import Console
from rstatus.models import JavaServerResponse, BedrockServerResponse
from mccolors import mcwrite
from voidxtool.auth import Authentication
from voidxtool.logs import LogsManager
from voidxtool.utilities.minecraft import ServerData, MineflayerKick
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg
from voidxtool.utilities.minecraft.get_bot_response import BotResponse
from voidxtool.utilities.input import Input
from voidxtool.utilities.scrapper.proxies import FreeProxies
from voidxtool.utilities.app_checker import AppChecker
from voidxtool.constants import VoidXToolConstants

console: Console = Console()

class KickCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="kick")
        self.target: Optional[str] = None
        self.version: Optional[str] = None
        self.username: Optional[str] = None
        self.logs_manager: Optional[LogsManager] = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        """
        Custom validation method to validate the kick command arguments.
        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        """
        self.target = user_arguments[0]
        self.version = user_arguments[1]
        self.username = user_arguments[2]
        
        if not (Validator.is_domain(self.target) or Validator.is_ip_and_port(self.target) or Validator.is_domain_and_port(self.target)):
            console.print(Msg.get('errors.invalidServer'))
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        """
        Run the kick command.
        :param arguments: list: The arguments to run the command
        :param authentication: Authentication: Auth object
        :return: bool: True if the command was executed successfully, False otherwise
        """
        if not self.validate_arguments(arguments):
            return False

        if not AppChecker.nodejs_installed():
            console.print(f"\n{VoidXToolConstants.SPACES}{VoidXToolConstants.PREFIX} [bright_white]NodeJS is not installed. Please install it and restart VoidXTool.")
            return False
        self.logs_manager = LogsManager(command_name=self.name)
        console.print(Msg.get(f"commands.{self.name}.messages.checkingServer").replace('%server%', self.target))
        self.logs_manager.write(f"Checking server: {self.target}")
        server_data = ServerData(target=self.target, bot=False).get_data()
        proxy = "-"

        if not server_data:
            console.print(Msg.get('errors.serverOffline'))
            self.logs_manager.write(f"Server offline: {self.target}\n")
            return False

        if isinstance(server_data, BedrockServerResponse):
            console.print(Msg.get('errors.notJavaServer'))
            self.logs_manager.write(f"Not a Java server: {self.target}\n")
            return False

        if ":" in self.target:
            ip_address, port = self.target.split(":")
        else:
            ip_address = self.target
            port = str(server_data.port)

        use_proxy = Input.get_input(
            input_message=Msg.get(f"commands.{self.name}.messages.proxyAsk"),
            input_type="boolean"
        )
        if not use_proxy:
            return False

        if use_proxy:
            use_custom_proxy = Input.get_input(
                input_message=Msg.get(f"commands.{self.name}.messages.customProxyAsk"),
                input_type="boolean"
            )
            if not use_custom_proxy:
                return False

            if use_custom_proxy:
                console.print(Msg.get(f"commands.{self.name}.messages.customProxy"))
                proxy = Input.get_input(
                    input_message=Msg.get(f"commands.{self.name}.messages.customProxy"),
                    input_type="proxy"
                )
                if not proxy:
                    return False
                if not FreeProxies.test_proxy(proxy=proxy):
                    console.print(Msg.get('errors.invalidProxy'))
                    self.logs_manager.write(f"Invalid proxy: {proxy}\n")
                    return False
            else:
                console.print(Msg.get(f"commands.{self.name}.messages.gettingFreeProxy"))
                proxy = FreeProxies().get_valid_proxy()
                if not proxy:
                    console.print(Msg.get(f"commands.{self.name}.messages.failedToGetFreeProxy"))
                    self.logs_manager.write("Failed to get a valid free proxy\n")
                    return False
                proxy = str(proxy)

        console.print(
            Msg.get(f"commands.{self.name}.messages.kicking")
            .replace('%server%', f"{ip_address}:{port}")
            .replace('%username%', self.username)
            .replace('%version%', self.version)
        )
        self.logs_manager.write(f"Calling MineflayerKick for {ip_address}:{port} with username {self.username} and version {self.version}")

        response = MineflayerKick(
            ip_address=ip_address,
            port=int(port),
            version=self.version,
            username=self.username,
            proxy=proxy
        ).get_response()

        self.logs_manager.write(f"Response: {response}")

        if response == "[BOT] Connected":
            console.print(
                Msg.get(f"commands.{self.name}.messages.playerKicked")
                .replace('%username%', self.username)
            )
            self.logs_manager.write(f"Player {self.username} kicked successfully\n")
        else:
            colored_response = BotResponse.get_bot_color_response(response=response)
            console.print(
                Msg.get(f"commands.{self.name}.messages.errorKickingPlayer")
                .replace('%username%', self.username)
                .replace('%reason%', "")
                .replace("", colored_response)
            )
            self.logs_manager.write(f"Error kicking player {self.username}: {response}\n")
            mcwrite(colored_response)

        return True