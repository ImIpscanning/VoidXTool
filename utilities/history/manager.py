import os
from typing import Optional
from loguru import logger
from rich.console import Console
from ezjsonpy import get_config_value
from voidxtool.gui.language import Msg
from voidxtool.files.path import VoidXToolPath
from voidxtool.constants import VoidXToolConstants

console: Console = Console()

class HistoryManager:
    __firstlineno__ = 15
    COMMANDS_TO_IGNORE: list = [
        'history',
        'help',
        'exit',
        'settings',
        'clear',
        'cls'
    ]

    @staticmethod
    def get_history(limit: Optional[int] = None):
        """
        Get the last N commands from the history file.
        :param limit: Optional[int] - Number of commands to retrieve.
        :return: list[str] - List of commands.
        """
        history_path = os.path.join(VoidXToolPath.get_voidxtool_data_path(), "history.txt")
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if not lines:
                return []
            if limit:
                lines = lines[-limit:]
            return [line.strip() for line in lines]
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.error(f"Error while reading history file: {e}")
            return []

    @staticmethod
    def get_10_last_commands():
        """
        Get the last 10 commands from the history file.
        :return: list[str] - List of last 10 commands.
        """
        return HistoryManager.get_history(10)

    @staticmethod
    def add_to_history(command: str):
        """
        Add a command to the history file.
        :param command: str - Command to add.
        """
        if command.split(' ')[0] in HistoryManager.COMMANDS_TO_IGNORE:
            return
        history_path = os.path.join(VoidXToolPath.get_voidxtool_data_path(), "history.txt")
        try:
            with open(history_path, "a", encoding="utf-8") as f:
                f.write(command.strip() + "\n")
        except Exception as e:
            logger.error(f"Error while writing to history file: {e}")

    __static_attributes__ = ()
