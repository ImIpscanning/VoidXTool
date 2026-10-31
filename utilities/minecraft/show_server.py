import time
import re
from typing import Union
import requests
from loguru import logger
from mccolors import mcwrite, mcremove
from rich.console import Console
from ezjsonpy import get_config_value
from rstatus.models import JavaServerResponse, BedrockServerResponse
from voidxtool.gui.language import Msg
from voidxtool.constants import VoidXToolConstants
from voidxtool.logs import LogsManager
console: Console = Console()

class CustomMessages:
    VULNERABLE_CHANNELS: list[str] = [
        'chatsentry:datasync',
        'plugin:cloudsync',
        'signedvelocity:main',
        'authmevelocity:main',
        'ecb:channel',
        'plugin:chcred',
        'atlas:out'
    ]

    @staticmethod
    def get_pluginchannels_message(message: str) -> str:
        if not message or len(message) == 0:
            return 'Plugin channels not found'
        return f"Plugin channels: {message}"

class Messages:
    def __init__(self):
        pass

    @staticmethod
    def get_server_message(server_data: Union[JavaServerResponse, BedrockServerResponse], server_command: bool) -> str:
        mode = get_config_value('serverShowMode', 'voidxtool') if server_command else get_config_value('serverShowMode', 'default')
        if isinstance(server_data, JavaServerResponse):
            msg = f"[Java] {server_data.ip}:{server_data.port} | MOTD: {server_data.motd} | Players: {server_data.players_online}/{server_data.players_max} | Version: {server_data.version}"
        elif isinstance(server_data, BedrockServerResponse):
            msg = f"[Bedrock] {server_data.ip}:{server_data.port} | MOTD: {server_data.motd} | Players: {server_data.players_online}/{server_data.players_max} | Version: {server_data.version}"
        else:
            msg = "Unknown server type"
        return msg

    @staticmethod
    def get_server_message_to_log(server_data: Union[JavaServerResponse, BedrockServerResponse]) -> str:
        msg = Messages.get_server_message(server_data, True)
        msg = mcremove(msg)
        msg = msg.replace('  ', '')
        return msg

class ShowMinecraftServer:
    @staticmethod
    def show(server_data: Union[JavaServerResponse, BedrockServerResponse], server_command: bool):
        msg = Messages.get_server_message(server_data, server_command)
        mcwrite(msg)

    @staticmethod
    def save_to_log(server_data: Union[JavaServerResponse, BedrockServerResponse], logs_manager: LogsManager):
        msg = Messages.get_server_message_to_log(server_data)
        logs_manager.save(msg)

    @staticmethod
    def send_to_webhook(server_data: Union[JavaServerResponse, BedrockServerResponse], webhook_url: str):
        msg = Messages.get_server_message_to_log(server_data)
        try:
            requests.post(webhook_url, json={"content": msg})
        except Exception as e:
            logger.error(f"Failed to send to webhook: {e}")