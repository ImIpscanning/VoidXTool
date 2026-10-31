
import random
import base64
import socket
from typing import Optional
import requests
import socks
from loguru import logger
from bs4 import BeautifulSoup, element
from requests import RequestException
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TaskID
from voidxtool.constants import VoidXToolConstants
from voidxtool.utilities.checker.socks import SocksChecker

console: Console = Console()

class FreeProxies:
    __firstlineno__ = 20

    def __init__(self):
        self.url = 'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=socks4&proxy_format=ipport&format=text&timeout=5015'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    def get_valid_proxy(self) -> Optional[str]:
        proxies = self.get_proxies()
        checker = SocksChecker(proxies=proxies)
        return checker.get_first_valid_proxy()

    def get_all_valid_proxies(self) -> list:
        proxies = self.get_proxies()
        checker = SocksChecker(proxies=proxies)
        return checker.get_all_valid_proxies()

    def get_proxies(self) -> list:
        urls = [
            'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=socks4&proxy_format=ipport&format=text&timeout=5015',
            'https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks4.txt',
            'https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt',
            'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt'
        ]
        proxies = []
        for url in urls:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    for line in response.text.splitlines():
                        line = line.strip()
                        if line and ':' in line:
                            proxies.append(line)
            except RequestException as e:
                logger.error(f'Error fetching proxies from {url}: {e}')
        return proxies

    def get_proxies_freeproxy_world(self, progress: Progress, task: TaskID) -> list:
        urls = [
            'https://www.freeproxy.world/?type=socks4&anonymity=&country=&speed=5000&port=&page=',
            'https://www.freeproxy.world/?type=socks5&anonymity=&country=&speed=5000&port=&page='
        ]
        proxies = []
        for base_url in urls:
            for page in range(1, 6):
                url = f'{base_url}{page}'
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        for row in soup.select('table tbody tr'):
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                ip = cols[0].get_text(strip=True)
                                port = cols[1].get_text(strip=True)
                                if ip and port:
                                    proxies.append(f'{ip}:{port}')
                except RequestException as e:
                    logger.error(f'Error fetching proxies from {url}: {e}')
                if progress:
                    progress.update(task, advance=1)
        return proxies

    def get_proxies_advanced_name(self, progress: Progress, task: TaskID) -> list:
        urls = [
            'https://advanced.name/freeproxy?type=socks4&page=',
            'https://advanced.name/freeproxy?type=socks5&page='
        ]
        proxies = []
        for base_url in urls:
            for page in range(1, 6):
                url = f'{base_url}{page}'
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        for row in soup.select('table tbody tr'):
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                ip = cols[0].get_text(strip=True)
                                port = cols[1].get_text(strip=True)
                                if ip and port:
                                    proxies.append(f'{ip}:{port}')
                except RequestException as e:
                    logger.error(f'Error fetching proxies from {url}: {e}')
                if progress:
                    progress.update(task, advance=1)
        return proxies

    @staticmethod
    def test_proxy(proxy: str) -> bool:
        try:
            ip, port = proxy.split(':')
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS4, ip, int(port))
            sock.settimeout(5)
            sock.connect(('8.8.8.8', 53))
            sock.close()
            return True
        except Exception as e:
            logger.error(f'Unexpected error while testing proxy: {e}')
            return False
