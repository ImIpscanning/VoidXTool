import subprocess
import time
import os
from typing import Optional, Union
from ezjsonpy import get_config_value
from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.padding import Padding
from rstatus.models import JavaServerResponse, BedrockServerResponse
from voidxtool.api.settings import APISettings
from voidxtool.logs import LogsManager
from voidxtool.utilities.minecraft import ServerData
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg
from voidxtool.utilities.input import Input
from voidxtool.utilities.scrapper.proxies import FreeProxies
from voidxtool.utilities.checker import SocksChecker
from voidxtool.files import VoidXToolPath
from voidxtool.constants import NodeJSConstants
from voidxtool.utilities import SendNotification
from voidxtool.auth.login import Authentication
from voidxtool.constants import VoidXToolConstants
from voidxtool.utilities.app_checker import AppChecker

console: Console = Console()

class BotAttackCommand(BaseCommand):
    def __init__(self):
        super().__init__(name='botattack')
        self.target = None
        self.version = None
        self.maxbots = None
        self.delay = None
        self.logs_manager = None
        self.bots_sent = 0
        self.bots_joined = 0
        self.bots_cant_join = 0
        self.bots_kicked = 0
        self.bots_proxy_timeout = 0

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.target = user_arguments[0]
        self.version = user_arguments[1]
        self.maxbots = user_arguments[2]
        self.delay = user_arguments[3]
        if not (Validator.is_domain(domain=self.target) or Validator.is_ip_and_port(ip=self.target) or Validator.is_domain_and_port(domain=self.target)):
            console.print(Msg.get('errors.invalidServer'))
            return False
        if not self.maxbots.isdigit() or not self.delay.isdigit():
            console.print(Msg.get('errors.invalidNumber'))
            return False
        self.maxbots = int(self.maxbots)
        self.delay = int(self.delay)
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        if not self.validate_arguments(arguments):
            return False
        self.custom_validate_arguments(arguments)
        self.logs_manager = LogsManager()
        proxies = FreeProxies.get()
        socks = SocksChecker.check(proxies)
        for i in range(self.maxbots):
            self.bots_sent += 1
            time.sleep(self.delay)
            joined = True
            if joined:
                self.bots_joined += 1
            else:
                self.bots_cant_join += 1
        return True

    def build_table(self):
        table = Table(box=SIMPLE_HEAVY)
        table.add_column('Bots Sent', justify='center', style='bright_yellow', no_wrap=True)
        table.add_column('Bots Joined', justify='center', style='bright_green', no_wrap=True)
        table.add_column('Bots Cant Join', justify='center', style='bright_red', no_wrap=True)
        table.add_column('Bots Kicked', justify='center', style='bright_red', no_wrap=True)
        table.add_column('Proxy timeout', justify='center', style='bright_red', no_wrap=True)
        table.add_row(
            str(self.bots_sent),
            str(self.bots_joined),
            str(self.bots_cant_join),
            str(self.bots_kicked),
            str(self.bots_proxy_timeout)
        )
        return Padding(table, (0, 0, 0, 2))

    __static_attributes__ = (
        'bots_cant_join',
        'bots_joined',
        'bots_kicked',
        'bots_proxy_timeout',
        'bots_sent',
        'delay',
        'logs_manager',
        'maxbots',
        'target',
        'version'
    )