import random
import socket
import time
from ipaddress import IPv4Address
from typing import Optional, Generator, List
from dataclasses import dataclass
from mccolors import mcwrite
from rich.console import Console
from voidxtool.utilities.scanner.ports import Ports
from voidxtool.utilities.rcon import MCRcon
from voidxtool.constants import VoidXToolConstants

console: Console = Console()

@dataclass
class IPRange:
    original_range: str
    ip_addresses: List[str]
    nmap_format: Optional[str] = None
    qubo_format: Optional[str] = None
    masscan_format: Optional[str] = None
    rustscan_format: Optional[str] = None

    def __post_init__(self):
        self.nmap_format = ','.join(self.ip_addresses)
        self.qubo_format = ','.join(self.ip_addresses)
        self.masscan_format = ','.join(self.ip_addresses)
        self.rustscan_format = ','.join(self.ip_addresses)

    def to_nmap_format(self) -> str:
        return self.nmap_format

    def to_qubo_format(self) -> str:
        return self.qubo_format

    def to_masscan_format(self) -> str:
        return self.masscan_format

    def to_rustscan_format(self) -> str:
        return self.rustscan_format

class ScannerUtils:
    @staticmethod
    def get_ips_in_range(range_str: str) -> Optional[IPRange]:
        ips = []
        parts = range_str.split(',')
        for part in parts:
            if '-' in part:
                start_ip, end_ip = part.split('-')
                ips.extend(list(ScannerUtils.generate_ip_range(start_ip.strip(), end_ip.strip())))
            else:
                if ScannerUtils.valid_ip_address(part.strip()):
                    ips.append(part.strip())
        if ips:
            return IPRange(original_range=range_str, ip_addresses=ips)
        return None

    @staticmethod
    def valid_ip_address(ip: str) -> bool:
        try:
            IPv4Address(ip)
            return True
        except Exception:
            return False

    @staticmethod
    def valid_ip_range_structure(range_str: str) -> bool:
        for part in range_str.split(','):
            if '-' in part:
                start_ip, end_ip = part.split('-')
                if not (ScannerUtils.valid_ip_address(start_ip.strip()) and ScannerUtils.valid_ip_address(end_ip.strip())):
                    return False
            else:
                if not ScannerUtils.valid_ip_address(part.strip()):
                    return False
        return True

    @staticmethod
    def ip_to_int(ip: str) -> int:
        return int(IPv4Address(ip))

    @staticmethod
    def generate_ip_range(start_ip: str, end_ip: str) -> Generator[str, None, None]:
        start = int(IPv4Address(start_ip))
        end = int(IPv4Address(end_ip))
        for ip_int in range(start, end + 1):
            yield str(IPv4Address(ip_int))

    @staticmethod
    def open_port(host: str, port: int, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    @staticmethod
    def get_unknown_port(port: int) -> Optional[str]:
        known_ports = {v for k, v in Ports.__dict__.items() if isinstance(v, int)}
        if port not in known_ports:
            return f"Unknown port: {port}"
        return None

    @staticmethod
    def show_unknown_port(ip_address: str, port: int, service: Optional[str] = None):
        time.sleep(random.random())
        msg = f"Unknown port detected: {ip_address}:{port}"
        if service:
            msg += f" ({service})"
        mcwrite(msg)