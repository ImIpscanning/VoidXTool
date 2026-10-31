from typing import Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table
from rich.padding import Padding
from rich.live import Live
from rich.text import Text
from rich.box import SIMPLE_HEAVY
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.commands.base import BaseCommand
from voidxtool.logs import LogsManager
from voidxtool.commands.validator import Validator
from voidxtool.utilities.ipv4 import IPInfo
from voidxtool.utilities.scrapper import DomainIPHistory

console: Console = Console()

class IPHistoryCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="iphistory")
        self.domain = ""
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments):
        '''
Custom validation method to validate the iphistory command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.domain = user_arguments[0]
        if not Validator.is_domain(self.domain):
            console.print(Msg.get(f"commands.{self.name}.messages.noIpHistory"))
            return False
        return True

    def run(self, arguments, authentication):
        '''
Run the iphistory command.

:param list arguments: The arguments to run the command
:param Authentication authentication: Auth object
:return bool: True if the command was executed successfully, False otherwise
'''
        if not self.validate_arguments(arguments):
            return False

        self.logs_manager = LogsManager(command_name=self.name)
        ip_history = DomainIPHistory(domain=self.domain).get_ip_history()

        if not ip_history or len(ip_history) == 0:
            console.print(Msg.get(f"commands.{self.name}.messages.noIpHistory"))
            return False

        table = Table(box=SIMPLE_HEAVY)
        table.add_column("IPs", justify="center")
        table.add_column("Organization", justify="center")
        padded_table = Padding(table, (0, 0, 0, 2))

        console.print(Msg.get(f"commands.{self.name}.messages.ipHistoryFound"))
        self.logs_manager.write(f"List of IPs and organizations found in the IP history of the domain: {self.domain}\n")

        with Live(padded_table, console=console, refresh_per_second=1):
            with ThreadPoolExecutor() as executor:
                future_to_ip = {executor.submit(self.fetch_ip_info, ip): ip for ip in ip_history}
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    ip_info = future.result()
                    org = ip_info[1][:20] if ip_info else "Unknown"
                    text = Text(org)

                    if "cloudflare" in org.lower():
                        text.stylize("bright_magenta")
                    elif "ovh" in org.lower():
                        text.stylize("green1")
                    elif org == "Unknown":
                        text.stylize("bright_red")

                    table.add_row(ip, text)
                    if self.logs_manager:
                        self.logs_manager.write(f"{ip} - {org}")

        console.print(
            Msg.get(f"commands.{self.name}.messages.ipHistoryEnd")
            .replace("%ips%", str(len(ip_history)))
            .replace("%domain%", self.domain)
        )
        self.logs_manager.write(f"End of the list of IPs and organizations found in the IP history of the domain: {self.domain}")
        return True

    def fetch_ip_info(self, ip_address):
        '''
Method to fetch the IP information
:param ip_address: The IP address
:return: The IP information
'''
        ip_info = IPInfo(ip_address=ip_address).get_info()
        self.logs_manager.write(f"IPInfo response: {ip_info}")
        if not ip_info:
            return ip_address, "Unknown"
        org = ip_info.get("org", "Unknown")
        if org.isspace() or org == "":
            org = "Unknown"
        return ip_address, org[:20]