import subprocess
import json
from subprocess import CompletedProcess
from typing import Optional
from ezjsonpy import get_config_value
from loguru import logger
from voidxtool.constants import VoidXToolConstants, NodeJSConstants

class MineflayerKick:
    def __init__(self, ip_address: str, port: int, version: str, username: Optional[str], proxy: str):
        self.ip_address = ip_address
        self.port = port
        self.version = str(version)
        self.username = username
        self.proxy = proxy
        self._response = ''

    def get_response(self) -> str:
        self._send_command()
        self._response = MCColor.get_text_from_json(self._response)
        self._response = self._response.replace('\n', '').replace('"', '').replace("'", '')
        return self._response

    def _send_command(self):
        command = self._get_command()
        try:
            result: CompletedProcess = subprocess.run(command, capture_output=True, text=True)
            self._response = result.stdout
        except Exception as e:
            logger.error(f"Error running mineflayer kick command: {e}")
            self._response = ''

    def _get_command(self) -> str:
        if self.version.startswith('-'):
            self.version = '47'
        node_path = get_config_value('node_path', NodeJSConstants.DEFAULT_NODE_PATH)
        script_path = VoidXToolConstants.MINEFLAYER_KICK_SCRIPT_PATH
        command = [
            node_path,
            script_path,
            '--ip', self.ip_address,
            '--port', str(self.port),
            '--version', self.version,
            '--username', self.username or '',
            '--proxy', self.proxy or ''
        ]
        return command

class BotResponse:
    @staticmethod
    def get_bot_color_response(response: str) -> str:
        if response == '&a&lConnected':
            return 'Connected'
        return 'Disconnected'

class MCColor:
    @staticmethod
    def replace_minecraft_color_codes(message: str) -> str:
        message = message.replace('&', '\u00A7')
        message = message.replace('§0', '[black]')
        message = message.replace('§1', '[blue]')
        message = message.replace('§2', '[green]')
        message = message.replace('§3', '[cyan]')
        message = message.replace('§4', '[red]')
        message = message.replace('§5', '[magenta]')
        message = message.replace('§6', '[yellow]')
        message = message.replace('§7', '[white]')
        message = message.replace('§8', '[bright_black]')
        message = message.replace('§9', '[bright_blue]')
        message = message.replace('§a', '[bright_green]')
        message = message.replace('§b', '[bright_cyan]')
        message = message.replace('§c', '[bright_red]')
        message = message.replace('§d', '[bright_magenta]')
        message = message.replace('§e', '[bright_yellow]')
        message = message.replace('§f', '[bright_white]')
        message = message.replace('§l', '[/strike][bold]')
        message = message.replace('§m', '[strike]')
        message = message.replace('§n', '[underline]')
        message = message.replace('§o', '[italic]')
        message = message.replace('§r', '[/]')
        return message

    @staticmethod
    def replace_mini_message_color_codes(message: str) -> str:
        replacements = {
            '<black>': '[black]',
            '<dark_blue>': '[blue]',
            '<dark_green>': '[green]',
            '<dark_aqua>': '[cyan]',
            '<dark_red>': '[red]',
            '<dark_purple>': '[magenta]',
            '<gold>': '[yellow]',
            '<gray>': '[white]',
            '<dark_gray>': '[bright_black]',
            '<blue>': '[bright_blue]',
            '<green>': '[bright_green]',
            '<aqua>': '[bright_cyan]',
            '<red>': '[bright_red]',
            '<light_purple>': '[bright_magenta]',
            '<yellow>': '[bright_yellow]',
            '<white>': '[bright_white]',
            '<bold>': '[bold]',
            '<italic>': '[italic]',
            '<underlined>': '[underline]',
            '<strikethrough>': '[strike]',
            '<reset>': '[/]',
        }
        for tag, rich in replacements.items():
            message = message.replace(tag, rich)
        return message

    @staticmethod
    def replace_mini_message_color_codes_with_minecraft_colors(message: str) -> str:
        replacements = {
            '<black>': '§0',
            '<dark_blue>': '§1',
            '<dark_green>': '§2',
            '<dark_aqua>': '§3',
            '<dark_red>': '§4',
            '<dark_purple>': '§5',
            '<gold>': '§6',
            '<gray>': '§7',
            '<dark_gray>': '§8',
            '<blue>': '§9',
            '<green>': '§a',
            '<aqua>': '§b',
            '<red>': '§c',
            '<light_purple>': '§d',
            '<yellow>': '§e',
            '<white>': '§f',
            '<bold>': '§l',
            '<italic>': '§o',
            '<underlined>': '§n',
            '<strikethrough>': '§m',
            '<reset>': '§r',
        }
        for tag, code in replacements.items():
            message = message.replace(tag, code)
        return message

    @staticmethod
    def get_text_from_json(json_str: str) -> str:
        try:
            obj = json.loads(json_str)
            result = ''
            def extract_text(extra):
                for part in extra:
                    if isinstance(part, dict):
                        if 'text' in part:
                            nonlocal result
                            result += part['text']
                        elif 'extra' in part:
                            extract_text(part['extra'])
            if isinstance(obj.get('extra'), list):
                extract_text(obj['extra'])
            elif 'text' in obj:
                result = obj['text']
            elif 'translate' in obj:
                result = obj.get('translate', '')
            return result.strip()
        except Exception:
            return ''
