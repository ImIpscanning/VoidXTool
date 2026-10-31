from typing import Optional
from rich.console import Console
from rich.table import Table
from voidxtool.commands.base import BaseCommand
from voidxtool.constants import VoidXToolConstants
from voidxtool.utilities.history.manager import HistoryManager

console: Console = Console()

class HistoryCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="history")
        self.limit = None

    def custom_validate_arguments(self, user_arguments):
        '''
Custom validation method to validate the iphistory command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.limit = user_arguments[0]
        try:
            self.limit = int(user_arguments[0])
            if self.limit < 1:
                console.print(f"\n{VoidXToolConstants.SPACES}{VoidXToolConstants.PREFIX} [bright_white]Enter a limit value greater than 0.")
                return False
        except ValueError:
            console.print(f"\n{VoidXToolConstants.SPACES}{VoidXToolConstants.PREFIX} [bright_white]Enter a valid limit value.")
            return False
        return True

    def run(self, arguments, authentication):
        '''
Run the history command.

:param list arguments: The arguments to run the command
:param Authentication authentication: Auth object
:return bool: True if the command was executed successfully, False otherwise
'''
        if not self.validate_arguments(arguments):
            return False
        entries = HistoryManager.get_history(self.limit)
        if not entries:
            console.print("[dim]Command history is empty.[/dim]")
            return True
        table = Table(title="Command history", show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Command", style="white")
        for index, entry in enumerate(entries, start=1):
            table.add_row(str(index), entry)
        console.print(table)
        return True
