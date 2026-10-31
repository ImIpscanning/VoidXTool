import json
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import requests
from bs4 import BeautifulSoup, element
from loguru import logger
from rich.console import Console
from voidxtool.logs import LogsManager
from voidxtool.files import VoidXToolPath
from voidxtool.gui.language import Msg
from voidxtool.constants import WebConstants

console = Console()

class MinecraftServerScrapper:
    def __init__(self, logs_manager: Optional[LogsManager] = None):
        self.logs_manager = logs_manager
        self.headers = {
            'User-Agent': random.choice(WebConstants.USER_AGENTS)
        }
        self.cookies = {
            'cookie_name': 'cookie_value'
        }
        config_path = VoidXToolPath.get_voidxtool_data_path() + '/mcserver-scrapper.json'
        try:
            with open(config_path, 'r') as file:
                self.file = file.read()
                self.servers = json.loads(self.file)['scrappers']
        except (json.JSONDecodeError, FileNotFoundError):
            self.servers = []
            logger.error('Failed to load the Minecraft server scrapper configuration file')
            if os.path.exists(config_path):
                os.remove(config_path)
        self.stop_event = threading.Event()
        self.server_list = []

    def get(self) -> list:
        max_workers = 15
        console.print(Msg.get('commands.websearch.messages.searchingWebsites'))
        if self.logs_manager:
            self.logs_manager.write('Started searching Minecraft servers in websites')
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for site in self.servers:
                url = site.get('url')
                pages = int(site.get('pages', 1))
                for page_num in range(1, pages + 1):
                    url_with_page = url.replace('%page%', str(page_num))
                    console.print(Msg.get('commands.websearch.messages.searchingInPage').replace('%page%', site.get('name', '')))
                    if self.stop_event.is_set():
                        return self.server_list
                    futures.append(executor.submit(self.scrape_page, url_with_page, site))
            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.server_list.extend(result)
        return self.server_list

    def scrape_page(self, url_with_page: str, server_page: dict) -> list:
        page = self.read_page(url_with_page)
        if page:
            return self.get_servers_in_page(page, server_page, url_with_page)
        return []

    def read_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = requests.get(url, headers=self.headers, cookies=self.cookies, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f'Error reading page: {e}')
        return None

    def get_servers_in_page(self, page: BeautifulSoup, server_page: dict, url: str) -> list:
        servers = []
        method = server_page.get('method', {})
        for selector in method.get('selectors', []):
            for server in page.select(selector):
                server_text = self._extract_server_text_method(server, method)
                if server_text:
                    servers.append(server_text)
        return servers

    def _extract_server_text_method(self, server: BeautifulSoup, method: dict) -> Optional[str]:
        try:
            if 'attribute' in method:
                return server.get(method['attribute'])
            elif 'text' in method:
                return server.get_text(strip=True)
        except AttributeError:
            pass
        return None

    def restore(self):
        self.stop_event.clear()

    def stop(self):
        self.stop_event.set()