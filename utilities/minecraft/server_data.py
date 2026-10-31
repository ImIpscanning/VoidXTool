from typing import Union
from rich.console import Console
from ezjsonpy import get_config_value
from rstatus import RStatusClient
from rstatus.models import JavaServerResponse, BedrockServerResponse
from voidxtool.gui.language import Msg
from voidxtool.utilities.minecraft.mcstatus_api import MCStatusIOAPI
from voidxtool.utilities.minecraft.get_bot_response import BotResponse, BotServerResponse
console: Console = Console()

class ServerData:
    def __init__(self, target: str, bot: bool, server_command: bool):
        self.target = target
        self.bot = bot
        self.server_command = server_command
        self._MODES = [
            'local',
            'mcstatus.io'
        ]

    def get_data(self) -> Union[JavaServerResponse, BedrockServerResponse, None]:
        mode = get_config_value('serverStatusGetMode', 'local')
        if get_config_value('debug', False):
            console.print(f"Server status get mode: {mode}")
        if mode == 'local':
            client = RStatusClient()
            response = client.get(self.target)
            if isinstance(response, (JavaServerResponse, BedrockServerResponse)):
                return response
            else:
                return None
        elif mode == 'mcstatus.io':
            api = MCStatusIOAPI()
            response = api.get(self.target)
            if isinstance(response, (JavaServerResponse, BedrockServerResponse)):
                return response
            else:
                return None
        else:
            console.print(Msg['errors.serverDataApiNotSet'])
            return None
