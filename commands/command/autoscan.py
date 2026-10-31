import time
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
from voidxtool.utilities.scanner.external import ExternalScanner
from voidxtool.utilities.input import Input
from voidxtool.utilities.time import TimeConverter
from voidxtool.constants import VoidXToolConstants

console: Console = Console()

class AutoScanCommand(BaseCommand):
    def __init__(self):
        super().__init__(name='autoscan')
        self.target_file = None
        self.port_range = None
        self.scan_method = None
        self.cooldown = None
        self.logs_manager = None
        self.servers_found = None
        self.external_scanner = None
        self.webhook_url = None
        self.targets = []

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.target_file = str(user_arguments[0])
        self.port_range = str(user_arguments[1])
        self.scan_method = str(user_arguments[2])
        self.cooldown = str(user_arguments[3])
        if not os.path.exists(self.target_file):
            console.print(Msg.get('errors.invalidFile'))
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        if not self.validate_arguments(arguments):
            return False
        self.custom_validate_arguments(arguments)
        self.logs_manager = LogsManager()
        self.external_scanner = ExternalScanner()
        self.webhook_url = get_config_value('webhook_url') if config_value_exists('webhook_url') else None
        self.targets = Input.load_targets(self.target_file)
        self.servers_found = []
        for target in self.targets:
            result = self.external_scanner.scan(target, self.port_range, self.scan_method)
            if result:
                self.servers_found.append(result)
            time.sleep(float(self.cooldown) if self.cooldown else 1)
        if self.webhook_url:
            WebhookUtils.send_results(self.webhook_url, self.servers_found)
        return True

    @staticmethod
    def show_timer(cooldown: Union[int, float, None]):
        if cooldown is None:
            return
        for i in range(int(cooldown), 0, -1):
            console.print(f"Cooldown: {i} seconds remaining")
            time.sleep(1)

    __static_attributes__ = (
        'cooldown',
        'external_scanner',
        'logs_manager',
        'port_range',
        'scan_method',
        'servers_found',
        'target_file',
        'targets',
        'webhook_url'
    )