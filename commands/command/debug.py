from rich.console import Console
from loguru import logger
from ezjsonpy import get_config_value, set_config_value
from voidxtool.commands.base import BaseCommand
from voidxtool.gui.language import Msg

console: Console = Console()

class DebugCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="debug")

    def run(self, arguments, authentication):
        '''
Run the debug command.

:param arguments: The arguments to run the command
:param authentication: The authentication object
:return bool: True if the command was executed successfully, False otherwise
'''
        debug_mode = get_config_value('debug')
        if debug_mode:
            console.print(Msg.get(f"commands.{self.name}.messages.debugDisabled"))
            set_config_value('debug', False)
            logger.info("Debug mode disabled")
        else:
            console.print(Msg.get(f"commands.{self.name}.messages.debugEnabled"))
            set_config_value('debug', True)
            logger.info("Debug mode enabled")
        return True