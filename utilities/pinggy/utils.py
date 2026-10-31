import socket
from typing import Union, Optional
from loguru import logger
from rich.console import Console
from ezjsonpy import get_config_value
from voidxtool.gui.language import Msg
console: Console = Console()

class PinggyIOUtils:
    @staticmethod
    @logger.catch
    def get_ip_port_from_string(domain: str) -> Optional[str]:
        '''
        Method to get the IP and port from a string
        :param domain: str: The domain to get the IP and port
        :return: Union[str, None]: The IP and port if the domain is valid, None otherwise
        '''
        try:
            if get_config_value('debug', False):
                print(f"Original domain: {domain}")
            if domain.startswith('tcp://'):
                domain = domain.replace('tcp://', '')
            if ':' not in domain:
                console.print(Msg.get('errors.portNotFoundInPinggyDomain'))
                return None
            ip_part, port_part = domain.split(':', 1)
            if get_config_value('debug', False):
                print(f"New domain: {ip_part}, port: {port_part}")
            ip_address = socket.gethostbyname(ip_part)
            if get_config_value('debug', False):
                print(f"IP Address resolved: {ip_address}")
            return f"{ip_address}:{port_part}"
        except Exception as e:
            console.print(Msg.get('errors.invalidPinggyDomain'))
            print(f"Error: {e}")
            return None
