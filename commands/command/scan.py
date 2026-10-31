import os
from typing import Optional, Union
from rich.console import Console
from ezjsonpy import get_config_value, config_value_exists
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.commands.base import BaseCommand
from voidxtool.logs import LogsManager
from voidxtool.commands.validator import Validator
from voidxtool.utilities.app_checker import AppChecker
from voidxtool.utilities.webhook import WebhookUtils
from voidxtool.utilities.minecraft import ServersFound, ServersDAT
from voidxtool.utilities.scanner.external import ExternalScanner
from voidxtool.utilities.scanner.utils import ScannerUtils, IPRange
from voidxtool.utilities.input import Input
from voidxtool.constants import VoidXToolConstants

console: Console = Console()

class ScanCommand(BaseCommand):
    def __init__(self):
        super().__init__('scan')
        self.target = None
        self.port_range = None
        self.scan_method = None
        self.original_target = None
        self.external_scanner = None
        self.logs_manager = None
        self.servers_found = None
        self.targets = None
        self.webhook_url = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
Custom validation method to validate the scan command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.target = user_arguments[0]
        self.port_range = user_arguments[1]
        self.scan_method = user_arguments[2]
        self.original_target = self.target

        if self.target.endswith('.txt'):
            if not os.path.exists(self.target):
                console.print(Msg.get('errors.invalidFile'))
                return False
        else:
            if not Validator.is_ip_or_range(self.target):
                console.print(Msg.get('errors.invalidIpOrRange'))
                return False

        if not ScannerUtils.validate_port_range(self.port_range):
            console.print(Msg.get('errors.invalidPortRange'))
            return False

        if not Validator.is_valid_scan_method(self.scan_method):
            console.print(Msg.get('errors.invalidScanMethod'))
            return False

        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
Run the scan command.

:param arguments: list: The arguments to run the command
:param authentication: Authentication: Auth object
:return: bool: True if the command was executed successfully, False otherwise
'''
        if not self.validate_arguments(arguments):
            return False

        self.logs_manager = LogsManager(command_name=self.name)
        self.servers_found = ServersFound()
        self.webhook_url = get_config_value('webhook_url') if config_value_exists('webhook_url') else None

        if self.target.endswith('.txt'):
            with open(self.target, 'r') as file:
                self.targets = [line.strip() for line in file if line.strip()]
        else:
            self.targets = IPRange(self.target).get_ips()

        self.external_scanner = ExternalScanner(
            targets=self.targets,
            port_range=self.port_range,
            scan_method=self.scan_method,
            logs_manager=self.logs_manager,
            servers_found=self.servers_found
        )

        console.print(Msg.get(f'commands.{self.name}.messages.scanning').replace('%target%', self.original_target))
        self.logs_manager.write(f'Scanning {self.original_target} with method {self.scan_method}...')
        
        self.external_scanner.scan()

        if self.servers_found.has_servers():
            console.print(Msg.get(f'commands.{self.name}.messages.serversFound').replace('%count%', str(len(self.servers_found))))
            if self.webhook_url:
                WebhookUtils.send_servers(self.webhook_url, self.servers_found, self.name)
        
        return True