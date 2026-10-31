import os
from datetime import datetime
from loguru import logger
from voidxtool.files import VoidXToolPath

class LogsManager:
    def __init__(self, command_name: str) -> None:
        """
        Initialize the LogsManager with a specific command name.
        This creates a folder for the logs if it doesn't exist already.

        :param command_name: The name of the command for which logs are being managed
        """
        log_dir = VoidXToolPath.get_voidxtool_data_path() + '/logs/' + command_name
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.command_name = command_name
        self.log_file_name = self.get_file_name()
        self.log_file_path = log_dir + '/' + self.log_file_name

    def write(self, message: str) -> None:
        """
        Write a log message to the log file.

        :param message: The message to log
        """
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(message + '\n')

    def get_file_name(self) -> str:
        """
        Generate and return the log file name based on the command name.
        If the command name is in a predefined list, the log file will include a timestamp.

        :return: The log file name
        """
        if self.command_name not in ('checker', 'iphistory', 'subdomains', 'websearch', 'scan', 'password'):
            return self.command_name + '.log'
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        return self.command_name + '_' + timestamp + '.log'