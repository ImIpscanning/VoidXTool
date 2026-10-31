import subprocess
import json
from subprocess import CompletedProcess
from typing import Optional
from dataclasses import dataclass
from ezjsonpy import get_config_value
from loguru import logger
# from voidxtool.utilities.minecraft.get_bot_response import GetBotUsernames
from voidxtool.constants import VoidXToolConstants, NodeJSConstants

@dataclass
class BotServerResponse:
    message: str
    brand: str
    pluginChannels: str

class BotResponse:
    def __init__(self, ip_address, port, version):
        self.ip_address = ip_address
        self.port = port
        self.version = str(version)
        self._response = ''

    @staticmethod
    def get_bot_color_response(response):
        if response == "&a&lConnected":
            return "&a&lConnected"
        return response

    def get_response(self):
        self._send_command()
        self._response = self._response.replace('\n', '').replace('"', '').replace("'", '')
        parts = self._response.split('/#VOIDXTOOL#/')
        if not parts or len(parts) < 3:
            return BotServerResponse(message='Error executing NodeJS command. See the logs for more information', brand='', pluginChannels='')
        return BotServerResponse(message=BotResponse.get_bot_color_response(parts[0]), brand=parts[1], pluginChannels=parts[2])

    def _send_command(self):
        command = self._get_command()
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                self._response = ''
            else:
                self._response = result.stdout
        except Exception:
            self._response = ''

    def _get_command(self):
        if self.version.startswith('-'):
            self.version = '47'
        return f"node {NodeJSConstants.BOT_SCRIPT_PATH} {self.ip_address} {self.port} {self.version}"