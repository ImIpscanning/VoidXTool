import random
import time
from dataclasses import dataclass
from typing import Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.table import Table
from rich.padding import Padding
from rich.text import Text
from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rstatus.models import JavaServerResponse, BedrockServerResponse
from rstatus.utils.response import BotResponse
from voidxtool.utilities.scanner.utils import ScannerUtils
from voidxtool.logs import LogsManager
from voidxtool.utilities.minecraft.server_data import ServerData
from voidxtool.utilities.minecraft.show_server import ShowMinecraftServer
from voidxtool.utilities.input.get_input import Input
from voidxtool.gui.language import Msg

console: Console = Console()

@dataclass
class ServersFound:
    count: int
    servers: list[str]
    only_bungee_vulnerable_servers: list[str]

@dataclass
class ServerFilters:
    only_cracked: bool
    description: Optional[str]
    min_online_players: Optional[int]
    protocol: Optional[int]

class GetServersData:
    def __init__(self, servers, webhook_url, logs_manager):
        self.servers = servers
        self.webhook_url = webhook_url
        self.servers_found = ServersFound(count=0, servers=[], only_bungee_vulnerable_servers=[])
        self.server_filters = ServerFilters(only_cracked=False, description=None, min_online_players=None, protocol=None)
        self.max_threads = 10
        self.executor = ThreadPoolExecutor(max_workers=self.max_threads)
        self.stopped = False
        self.logs_manager = logs_manager

    def get_servers(self):
        if len(self.servers) == 0:
            raise ValueError('The servers list is empty')
        results = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_server = {executor.submit(self._get_server_data, server): server for server in self.servers}
            for future in as_completed(future_to_server):
                server = future_to_server[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception:
                    pass
        self.servers_found.count = len(results)
        self.servers_found.servers = results
        return self.servers_found

    def get_server(self, server):
        return self._get_server_data(server)

    def ask_filters(self, show_table=True):
        if show_table:
            self._show_table()
        only_cracked = Input(input_message=Msg.get('filterServers.filterByOnlyBotCanJoin'), input_type='boolean').get_input()
        description = Input(input_message=Msg.get('filterServers.description'), input_type='text').get_input()
        min_online_players = Input(input_message=Msg.get('filterServers.onlinePlayers'), input_type='int').get_input()
        protocol = Input(input_message=Msg.get('filterServers.protocol'), input_type='int').get_input()
        self.server_filters = ServerFilters(
            only_cracked=only_cracked,
            description=description,
            min_online_players=min_online_players,
            protocol=protocol
        )

    def _show_table(self):
        table = Table(box=SIMPLE_HEAVY)
        table.add_column(Msg.get('filterServers.onlyBotCanJoin'), justify='center', style='bright_yellow', no_wrap=True)
        table.add_column(Msg.get('filterServers.description'), justify='center', style='bright_white', no_wrap=True)
        table.add_column(Msg.get('filterServers.onlinePlayers'), justify='center', style='bright_white', no_wrap=True)
        table.add_column(Msg.get('filterServers.protocol'), justify='center', style='bright_cyan', no_wrap=True)
        only_cracked_text = Text('✅', style='green') if self.server_filters.only_cracked else Text('❌', style='red')
        table.add_row(
            str(only_cracked_text),
            str(self.server_filters.description or ''),
            str(self.server_filters.min_online_players or ''),
            str(self.server_filters.protocol or '')
        )
        console.print(table)

    def _get_server_data(self, server):
        if self.stopped:
            return None
        return server