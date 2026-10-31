import socket
import socks
from time import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeRemainingColumn
from loguru import logger
from voidxtool.gui.language import Msg

console: Console = Console()

class SocksChecker:
    __firstlineno__ = 16

    def __init__(self, proxies: List[str]):
        """
        Initialize the SocksChecker class with a list of proxies.

        :param proxies: A list of proxies to check, each in the format 'ip:port'.
        """
        self.proxies = proxies
        self.stopped = False
        self.executor = None

    @staticmethod
    def is_valid_proxy(proxy: str) -> bool:
        """
        Check if the proxy is valid
        :param proxy: str
        :return: bool - True if the proxy is valid, False otherwise
        """
        try:
            ip, port = proxy.split(":")
            socket.inet_aton(ip)
            port = int(port)
            if port < 1 or port > 65535:
                return False
            return True
        except (ValueError, OSError):
            return False

    def _check_proxy(self, proxy: str, timeout: int = 10) -> Tuple[bool, float]:
        '''
        Check if the proxy is valid by attempting a connection.
        :param proxy: str
        :param timeout: int
        :return: Tuple[bool, float] - True if the proxy is valid, False otherwise, and response time
        '''
        if self.stopped:
            return False, 0.0
        try:
            ip, port = proxy.split(":")
            port = int(port)
            start_time = time()
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, ip, port)
            s.settimeout(timeout)
            s.connect(("8.8.8.8", 53))
            s.close()
            elapsed = time() - start_time
            return True, elapsed
        except Exception as e:
            logger.debug(f"Proxy {proxy} failed: {e}")
            return False, 0.0

    def get_all_valid_proxies(self) -> List[str]:
        '''
        Check all the proxies in the list and return all valid proxies
        :return: List[str] - List of valid proxies
        '''
        valid_proxies = []
        if not self.proxies or len(self.proxies) == 0:
            return []
        with Progress("[progress.description]{task.description}", BarColumn(), TimeRemainingColumn()) as progress:
            task = progress.add_task("Checking proxies...", total=len(self.proxies))
            with ThreadPoolExecutor(max_workers=min(32, len(self.proxies))) as executor:
                futures = {executor.submit(self._check_proxy, proxy): proxy for proxy in self.proxies}
                for future in as_completed(futures):
                    proxy = futures[future]
                    try:
                        is_valid, _ = future.result()
                        if is_valid:
                            valid_proxies.append(proxy)
                    except Exception as e:
                        logger.debug(f"Error checking proxy {proxy}: {e}")
                    progress.advance(task)
        return valid_proxies

    def get_first_valid_proxy(self) -> Optional[str]:
        '''
        Return the first valid proxy found without waiting for others
        :return: str - The first valid proxy or None if none is found
        '''
        if not self.proxies or len(self.proxies) == 0:
            return None
        with ThreadPoolExecutor(max_workers=min(32, len(self.proxies))) as executor:
            futures = {executor.submit(self._check_proxy, proxy): proxy for proxy in self.proxies}
            for future in as_completed(futures):
                proxy = futures[future]
                try:
                    is_valid, _ = future.result()
                    if is_valid:
                        return proxy
                except Exception as e:
                    logger.debug(f"Error checking proxy {proxy}: {e}")
        return None

    __static_attributes__ = ('executor', 'proxies', 'stopped')