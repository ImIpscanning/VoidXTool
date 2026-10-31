from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union, Optional
import requests
from loguru import logger
from rich.console import Console
from rstatus.models import JavaServerResponse, BedrockServerResponse
from rstatus.models.java_server_data import MOTD as JavaMOTD, Version as JavaVersion, Players as JavaPlayers, ModInfo
from rstatus.models.bedrock_server_data import MOTD as BedrockMOTD, Version as BedrockVersion, Players as BedrockPlayers
from rstatus.utils.clear import ClearResponse
from rstatus.protocol.version import ProtocolVersion
from voidxtool.gui.language import Msg
from voidxtool.utilities.minecraft.get_bot_response import BotResponse, BotServerResponse

console: Console = Console()

class MCStatusIOAPI:
    def __init__(self, target: str, bot: bool, server_command: bool):
        self.target = target
        self.bot = bot
        self.server_command = server_command
        self.java_endpoint = 'https://api.mcstatus.io/v2/status/java/'
        self.bedrock_endpoint = 'https://api.mcstatus.io/v2/status/bedrock/'

    def get(self) -> Union[JavaServerResponse, BedrockServerResponse, None]:
        if self.server_command == 'java':
            return self._send_java_request()
        elif self.server_command == 'bedrock':
            return self._send_bedrock_request()
        else:
            logger.error('Unknown server command type')
            return None

    def _send_java_request(self) -> Union[JavaServerResponse, None]:
        try:
            response = requests.get(f'{self.java_endpoint}{self.target}')
            if response.status_code != 200:
                return None
            data = response.json()
            return self._convert_data(data, 'java')
        except Exception as ex:
            logger.error(f'Error sending the request to the MCStatus.io API (Java): {ex}')
            return None

    def _send_bedrock_request(self) -> Union[BedrockServerResponse, None]:
        try:
            response = requests.get(f'{self.bedrock_endpoint}{self.target}')
            if response.status_code != 200:
                return None
            data = response.json()
            return self._convert_data(data, 'bedrock')
        except Exception as ex:
            logger.error(f'Error sending the request to the MCStatus.io API (Bedrock): {ex}')
            return None

    def _convert_data(self, data: dict, server_type: str) -> Union[JavaServerResponse, BedrockServerResponse, None]:
        if not data.get('online'):
            return None
        if server_type == 'java':
            return JavaServerResponse(
                motd=data.get('motd'),
                version=data.get('version'),
                players=data.get('players'),
                modinfo=data.get('modinfo')
            )
        elif server_type == 'bedrock':
            return BedrockServerResponse(
                motd=data.get('motd'),
                version=data.get('version'),
                players=data.get('players')
            )
        return None

    @staticmethod
    def _get_players(players: list) -> list:
        return players if players else []