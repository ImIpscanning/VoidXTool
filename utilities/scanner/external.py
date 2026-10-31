import subprocess
import threading
import os
import re
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from ezjsonpy import get_config_value
from rich.console import Console
from loguru import logger
from voidxtool.gui.language import Msg
from voidxtool.utilities.minecraft.get_servers import GetServersData, ServersFound
from voidxtool.files import VoidXToolPath
from voidxtool.logs import LogsManager

console: Console = Console()

class ExternalScanner:
    def __init__(
        self,
        target: str,
        port_range: str,
        scan_method: str,
        logs_manager: LogsManager,
        webhook_url: Optional[str],
        skip_servers: Optional[List[str]]
    ):
        """
        Initialize the ExternalScanner class
        :param target: str: The target to scan
        :param port_range: str: The port range to scan
        :param scan_method: str: The scan method to use
        """
        self.target = target
        self.port_range = port_range
        self.scan_method = scan_method
        self.logs_manager = logs_manager
        self.webhook_url = webhook_url
        self.skip_servers = skip_servers
        self.get_servers_data = GetServersData(webhook_url=self.webhook_url, logs_manager=logs_manager)
        self.scan_commnand = None
        self.command_output = ''
        self.process = None
        self.semaphore = threading.Semaphore()
        self.executor = None
        self.stopped = False
        self.first_line = True
        self.get_servers_data.ask_filters()

    def scan(self) -> Optional[ServersFound]:
        """
        Method to start the scan
        :return: ServersFound: The servers found
        """
        self.scan_commnand = self._get_scan_command()
        text_to_search, pattern, invalid_ip_texts, invalid_ports_texts = self._get_scan_params()
        servers_found = self._start_scan(text_to_search, pattern, invalid_ip_texts, invalid_ports_texts)
        return servers_found

    def _start_scan(self, text_to_search, pattern, invalid_ip_texts, invalid_ports_texts):
        """
        Start the scanner process
        :param str text_to_search: Text to search for ports
        :param str pattern: Port pattern
        :param list invalid_ip_texts: Texts to search for invalid ip
        :param list invalid_ports_texts: Texts to search for invalid port range
        """
        if get_config_value('debug'):
            print(self.scan_commnand)
        self.process = subprocess.Popen(
            self.scan_commnand,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        )
        self.executor = ThreadPoolExecutor(max_workers=15)
        servers_found = []
        try:
            for line in self.process.stdout:
                line = line.decode('utf-8', errors='replace').strip()
                self.command_output += line + '\n'
                if any(err in line for err in invalid_ip_texts):
                    logger.error(f"Invalid IP detected: {line}")
                    continue
                if any(err in line for err in invalid_ports_texts):
                    logger.error(f"Invalid port range detected: {line}")
                    continue
                match = self._extract_server_info(line, pattern)
                if match:
                    servers_found.append(match)
                    logger.info(f"Found server: {match}")
        finally:
            self.process.stdout.close()
            self.process.wait()
            self.executor.shutdown(wait=False)
        return ServersFound(servers_found)

    def _get_scan_command(self) -> Optional[str]:
        """
        Get the command to scan the target.
        :return: The command to scan the target.
        """
        if self.scan_method == 'nmap':
            return f"nmap -p {self.port_range} {self.target} --open"
        elif self.scan_method == 'masscan':
            return f"masscan {self.target} -p{self.port_range} --rate=1000"
        elif self.scan_method == 'qubo':
            return f"qubo -range {self.target} -ports {self.port_range}"
        elif self.scan_method == 'old_qubo':
            return f"old_qubo -range {self.target} -ports {self.port_range}"
        elif self.scan_method == 'rustscan':
            return f"rustscan -a {self.target} -p {self.port_range}"
        else:
            logger.error(f"Unknown scan method: {self.scan_method}")
            return None

    def _get_scan_params(self):
        """
        Get the scan parameters.
        :return: The scan parameters.
        """
        params = {
            'nmap': (
                'Discovered open port',
                r'open port (\d+)/\w+ on (\d+\.\d+\.\d+\.\d+)',
                ['Failed to resolve "'],
                ['Your port specifications are illegal.', 'Your port range']
            ),
            'masscan': (
                'Discovered open port',
                r'open port (\d+)/\w+ on (\d+\.\d+\.\d+\.\d+)',
                ['ERROR: bad IP address/range:', 'unknown command-line parameter'],
                ['bad target port:']
            ),
            'old_qubo': (
                ')(',
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b',
                ['Invalid IP range.'],
                ['port is out of range', 'For input string:']
            ),
            'qubo': (
                ')(',
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b',
                ['Invalid IP range.', 'usage: -range <arg> -ports'],
                ['port is out of range', 'For input string:', 'usage: -range <arg> -ports']
            ),
            'rustscan': (
                'Open',
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b',
                ['No IPs could be resolved, aborting scan'],
                ["for '--ports <PORTS>':", 'is not in 0..=65535', '--range <RANGE>']
            )
        }
        return params.get(self.scan_method, ('', '', [], []))

    def _extract_server_info(self, output_line: str, pattern: str) -> Optional[str]:
        """
        Extract the server information from the output line.
        :param output_line: Output line to extract the server information.
        :param pattern: Pattern to extract the server information.
        :return: The server information.
        """
        match = re.search(pattern, output_line)
        if match:
            return match.group(0)
        return None