import uuid
from typing import Optional
from rich.console import Console
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.commands.base import BaseCommand
from voidxtool.utilities.minecraft import PlayerUUID, PlayerUUIDFormat, PlayerUsername
from voidxtool.logs import LogsManager

console: Console = Console()

class UuidCommand(BaseCommand):
    """
    Command to handle UUID and username lookups for Minecraft players.
    """
    def __init__(self):
        """
        Initialize the UuidCommand with the base command name and default attributes.
        """
        super().__init__(name="uuid")
        self.logs_manager: Optional[LogsManager] = None
        self.target: str = ""

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        """
        Validate the UUID command arguments.

        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        """
        if len(user_arguments) < 1:
            console.print(Msg.get("errors.invalidArguments"))
            return False
        self.target = user_arguments[0]
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        """
        Run the UUID command.

        :param arguments: list: The arguments to run the command
        :param authentication: Authentication: Auth object
        :return: bool: True if the command was executed successfully, False otherwise
        """
        if not self.validate_arguments(arguments):
            return False

        self.logs_manager = LogsManager(command_name=self.name)

        if len(self.target) == 36:
            self.target = self.target.replace("-", "")
        if len(self.target) == 32:
            self._show_username()
        else:
            self._show_uuid()

        return True

    def _show_username(self) -> None:
        """
        Show the username corresponding to a given UUID.
        """
        console.print(
            Msg.get(f"commands.{self.name}.messages.gettingUsername").replace("%uuid%", self.target)
        )
        self.logs_manager.write(f"Getting the username for the UUID: {self.target}")

        player = PlayerUsername(uuid=self.target)
        username = player.get_username()

        if username is None:
            console.print(
                Msg.get(f"commands.{self.name}.messages.usernameNotFound")
            )
            self.logs_manager.write(f"The player with the UUID {self.target} was not found")
        else:
            console.print(
                Msg.get(f"commands.{self.name}.messages.username")
                .replace("%username%", f"[bright_green]{username}[/bright_green]")
            )
            self.logs_manager.write(f"The username for the UUID {self.target} is {username}")

    def _show_uuid(self) -> None:
        """
        Show the UUID(s) corresponding to a given username.
        """
        console.print(
            Msg.get(f"commands.{self.name}.messages.gettingUUID").replace("%username%", self.target)
        )
        self.logs_manager.write(f"Getting the UUID for the username: {self.target}")

        print("")
        player = PlayerUUID(username=self.target)
        uuid_data = player.get_uuid()

        if uuid_data.online_uuid:
            console.print(
                Msg.get(f"commands.{self.name}.messages.uuid")
                .replace("%uuid%", f"[bright_green]{uuid_data.online_uuid}[/bright_green]")
                .replace("%uuidVariant%", f"[bright_green]{uuid.UUID(uuid_data.online_uuid)}[/bright_green]")
            )
            self.logs_manager.write(f"Online UUID: {uuid_data.online_uuid}")

        if uuid_data.offline_uuid:
            console.print(
                Msg.get(f"commands.{self.name}.messages.uuid")
                .replace("%uuid%", f"[bright_red]{uuid_data.offline_uuid}[/bright_red]")
                .replace("%uuidVariant%", f"[bright_red]{uuid.UUID(uuid_data.offline_uuid)}[/bright_red]")
            )
            self.logs_manager.write(f"Offline UUID: {uuid_data.offline_uuid}")