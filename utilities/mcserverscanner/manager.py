import random
import socket
import struct
import time
from typing import Optional
import requests
from ezjsonpy import get_config_value
from requests import Response
from loguru import logger
from rich.console import Console
from voidxtool.gui.language import Msg
from voidxtool.utilities.minecraft.get_servers import GetServersData, ServersFound
from voidxtool.logs import LogsManager

console: Console = Console()

class MCServerScanner:
    def __init__(self, min_servers, command_name, logs_manager):
        self.api = 'https://api.cornbread2100.com/servers?limit=100'
        self.logs_manager = logs_manager
        self.get_servers_data = GetServersData(webhook_url=None, logs_manager=logs_manager)
        self.server_data_manager = GetServersData(servers=[], logs_manager=logs_manager)
        self.min_servers = min_servers
        self.command_name = command_name

    def get_servers(self) -> Optional[ServersFound]:
        self.server_data_manager.ask_filters()
        servers = []
        retries = 0
        max_retries = 5
        while retries < max_retries:
            servers = self._send_request()
            if servers is None:
                logger.warning("API rate limited, retrying...")
                time.sleep(2)
                retries += 1
                continue
            if len(servers) >= self.min_servers:
                logger.info(f"Found {len(servers)} servers.")
                return ServersFound(servers)
            logger.info(f"Found {len(servers)} servers (less than minimum required), retrying...")
            time.sleep(2)
            retries += 1
        logger.error("Failed to find enough servers after retries.")
        return None

    def _send_request(self) -> Optional[list]:
        try:
            response = requests.get(self.api, timeout=10)
            if response.status_code == 429:
                logger.warning("Rate limited by the API.")
                return None
            data = response.json()
            if isinstance(data, list):
                return data
            return []
        except ValueError as e:
            logger.error(f"Requests failed in MCServerScanner. Failed to parse JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Requests failed in MCServerScanner: {e}")
            return []

    @staticmethod
    def int_to_ip(ip_int: int) -> str:
        return socket.inet_ntoa(struct.pack('!I', ip_int))

    @staticmethod
    def get_random_skip() -> int:
        return random.randint(0, 50) * 100