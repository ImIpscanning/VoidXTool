import re
import requests
from typing import Optional, List
from bs4 import BeautifulSoup
from bs4.element import PageElement, NavigableString, Tag
from rich.console import Console
from voidxtool.gui.language import Msg

console: Console = Console()

class DomainIPHistory:
    def __init__(self, domain: str):
        """
        Initialize the DomainIPHistory class with the provided domain.
        :param domain: The domain for which the IP history will be fetched
        """
        self.domain = domain
        self.url = f"https://viewdns.info/iphistory/?domain={self.domain}"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    def get_ip_history(self) -> Optional[List[str]]:
        """
        Get the IP history of the domain by scraping data from the specified URL.
        :return: A list of IP addresses if found, an empty list if no IPs are found, or None if there is a connection error.
        """
        console.print(Msg.get('commands.iphistory.messages.gettingIpHistory'))
        try:
            response = requests.get(self.url, headers=self.headers)
            if response.status_code != 200:
                console.print(Msg.get('commands.iphistory.messages.noIpHistory'))
                return []
            soup = BeautifulSoup(response.text, 'html.parser')
            tbody = soup.find('tbody', class_='bg-white')
            if not tbody:
                console.print(Msg.get('commands.iphistory.messages.noIpHistory'))
                return []
            ip_list = []
            for tr in tbody.find_all('tr'):
                tds = tr.find_all('td')
                if tds and len(tds) > 0:
                    ip_text = tds[0].get_text(strip=True)
                    if re.match(r'^\d{1,3}(?:\.\d{1,3}){3}$', ip_text):
                        ip_list.append(ip_text)
            return ip_list
        except requests.exceptions.RequestException:
            console.print(Msg.get('errors.endpointConnectionError'))
            return None