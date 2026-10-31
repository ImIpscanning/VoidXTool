import os
from rich.console import Console
from voidxtool.commands.base import BaseCommand
from voidxtool.gui.banners import VoidXToolBanner

console: Console = Console()

class ClearCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="clear")

    def run(self, arguments, authentication):
        '''
Clear the screen and show the banner.

:param list arguments: The arguments to run the command
:param authentication: Auth object
:return bool: True if the command was executed successfully, False otherwise
'''
        os.system('cls' if os.name == 'nt' else 'clear')
        VoidXToolBanner.show_voidxtool_banner(auth=authentication)
        return True