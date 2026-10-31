from rich.console import Console
from voidxtool.commands.base import BaseCommand
from voidxtool.gui.language import Msg
from voidxtool.utilities.minecraft import ServersDAT
from voidxtool.utilities.termux import TermuxUtilities

console: Console = Console()

class ClearServersCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="clearservers")

    def custom_validate_arguments(self, user_arguments):
        '''
Custom validation method to validate the customport command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        return True

    def run(self, arguments, authentication):
        '''
Run the seeker command.

:param list arguments: The arguments to run the command
:param Authentication authentication: Auth object
:return bool: True if the command was executed successfully, False otherwise
'''
        if TermuxUtilities.is_termux():
            console.print(Msg.get('errors.commandNotSupportedInTermuxAndroid'))
            return False
        console.print(Msg.get(f"commands.{self.name}.messages.serversCleared"))
        ServersDAT().remove_servers_dat_file()
        return True