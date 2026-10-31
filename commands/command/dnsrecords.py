import time
from typing import Optional
from rich.console import Console
from rich.padding import Padding
from rich.box import SIMPLE_HEAVY
from rich.table import Table
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.utilities.dns_records import GetDNSRecords
from voidxtool.logs import LogsManager

console: Console = Console()

class DnsRecordsCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="dnsrecords")
        self.domain = None
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments):
        '''
Custom validation method to validate the dnsrecords command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.domain = str(user_arguments[0])
        if not Validator.is_domain(domain=self.domain):
            console.print(Msg.get('errors.invalidDomain'))
            return False
        return True

    def run(self, arguments, authentication):
        '''
Run the seeker command.

:param list arguments: The arguments to run the command
:param Authentication authentication: Auth object
:return bool: True if the command was executed successfully, False otherwise
'''
        if not self.validate_arguments(arguments):
            return False

        console.print(Msg.get(f"commands.{self.name}.messages.lookingUpDnsRecords").replace("%domain%", self.domain))
        time.sleep(0.5)
        self.logs_manager = LogsManager(command_name=self.name)
        self.logs_manager.write(f"Looking up DNS records for the domain: {self.domain}")
        
        dns_records = GetDNSRecords(self.domain).get_dns_records()
        
        if len(dns_records) == 0:
            console.print(Msg.get(f"commands.{self.name}.messages.noDnsRecords"))
            return False
        
        table = Table(box=SIMPLE_HEAVY)
        table.add_column("DNS Record", justify="center")
        table.add_column("Value", justify="center")
        
        padded_table = Padding(table, (0, 0, 0, 2))
        
        for record in dns_records:
            for value in record['value']:
                if self.logs_manager:
                    self.logs_manager.write(f"{record['type']}: {value}")
                table.add_row(record['type'], value)
        
        console.print(padded_table)
        
        records_count = len(dns_records)
        console.print(Msg.get(f"commands.{self.name}.messages.dnsRecordsEnd").replace("%domain%", self.domain).replace("%records%", str(records_count)))
        
        if self.logs_manager:
            self.logs_manager.write(f"Found {records_count} DNS records for the domain: {self.domain}\n")
        
        return True