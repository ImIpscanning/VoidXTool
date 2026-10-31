
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from rich.console import Console
from voidxtool.gui.language import Msg
from voidxtool.utilities.minecraft import GetServersData, ServersFound
from voidxtool.utilities.termux import TermuxUtilities

console: Console = Console()

class TCPListener:
    __firstlineno__ = 14

    def __init__(self):
        self.ip_port_found = []
        self.futures = []
        self.executor = ThreadPoolExecutor(max_workers=15)
        self.get_servers_data = GetServersData()

    def packet_callback(self, packet):
        try:
            if TermuxUtilities.is_termux():
                return
            from scapy.all import TCP, IP
            if packet.haslayer(TCP):
                ip = packet[IP].dst
                port = packet[TCP].dport
                ip_port = f"{ip}:{port}"
                if ip_port not in self.ip_port_found:
                    self.ip_port_found.append(ip_port)
                    future = self.executor.submit(self.get_servers_data.get_server, ip, port)
                    self.futures.append(future)
        except Exception as e:
            logger.error(f"Error in packet_callback: {e}")

    def get_minecraft_servers(self) -> Optional[ServersFound]:
        try:
            if TermuxUtilities.is_termux():
                return None
            from scapy.all import sniff
            console.print(Msg.get('commands.mclistener.messages.start'))
            sniff(filter='tcp', prn=self.packet_callback, store=0)
            return self.get_servers_data.servers_found
        except PermissionError:
            logger.error('Permission denied, try running as root')
            return None
        except Exception as e:
            logger.error(f"Error in get_minecraft_servers: {e}")
            return None