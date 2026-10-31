from typing import Optional
from rich.console import Console
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.commands.base import BaseCommand
from voidxtool.logs import LogsManager
from voidxtool.commands.validator import Validator
from voidxtool.utilities.ipv4 import IPInfo, IPInfoFormat

console: Console = Console()

class IPInfoCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="ipinfo")
        self.ip_address = ""
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments):
        '''
        Custom validation method to validate the ipinfo command arguments.
        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        '''
        self.ip_address = user_arguments[0]
        if not Validator.is_ip_address(self.ip_address):
            console.print(Msg.get('errors.invalidIpFormat').replace('%ip%', self.ip_address))
            return False
        return True

    def run(self, arguments, authentication):
        '''
        Run the ipinfo command.
        :param list arguments: The arguments to run the command
        :param Authentication authentication: Auth object
        :return bool: True if the command was executed successfully, False otherwise
        '''
        if not self.validate_arguments(arguments):
            return False

        self.logs_manager = LogsManager(command_name=self.name)
        console.print(Msg.get(f"commands.{self.name}.messages.gettingIpData"))
        self.logs_manager.write(f"Getting IP information for the IP address: {self.ip_address}")

        ip_info = IPInfo(ip_address=self.ip_address).get_info()

        if not ip_info:
            console.print(Msg.get(f"commands.{self.name}.messages.error"))
            self.logs_manager.write(f"Error getting IP information for the IP address: {self.ip_address}\n")
            return False

        console.print(
            Msg.get(f"commands.{self.name}.messages.continent")
            .replace('%continent%', ip_info.get('continent', ''))
            .replace('%continentCode%', ip_info.get('continent_code', ''))
        )
        console.print(
            Msg.get(f"commands.{self.name}.messages.country")
            .replace('%country%', ip_info.get('country', ''))
            .replace('%countryCode%', ip_info.get('country_code', ''))
        )
        console.print(
            Msg.get(f"commands.{self.name}.messages.region")
            .replace('%region%', ip_info.get('region', ''))
            .replace('%regionName%', ip_info.get('region_name', ''))
        )
        console.print(
            Msg.get(f"commands.{self.name}.messages.city")
            .replace('%city%', ip_info.get('city', ''))
        )
        console.print(
            Msg.get(f"commands.{self.name}.messages.timezone")
            .replace('%timezone%', ip_info.get('timezone', ''))
        )
        console.print(
            Msg.get(f"commands.{self.name}.messages.isp")
            .replace('%isp%', ip_info.get('isp', ''))
        )
        console.print(
            Msg.get(f"commands.{self.name}.messages.organization")
            .replace('%organization%', ip_info.get('org', ''))
        )

        if self.logs_manager:
            self.logs_manager.write(
                f"IP information for the IP address: {self.ip_address}\n"
                f"Continent: {ip_info.get('continent', '')} ({ip_info.get('continent_code', '')})\n"
                f"Country: {ip_info.get('country', '')} ({ip_info.get('country_code', '')})\n"
                f"Region: {ip_info.get('region', '')} ({ip_info.get('region_name', '')})\n"
                f"City: {ip_info.get('city', '')}\n"
                f"Timezone: {ip_info.get('timezone', '')}\n"
                f"ISP: {ip_info.get('isp', '')}\n"
                f"Organization: {ip_info.get('org', '')}\n"
            )

        return True