import os
import time
import socket
from typing import Optional, Union
from threading import Lock, BoundedSemaphore
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.live import Live
from rich.text import Text
from loguru import logger
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.commands.base import BaseCommand
from voidxtool.logs import LogsManager
from voidxtool.commands.validator import Validator

console = Console()

class SubdomainsCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="subdomains")
        self.domain = None
        self.file = None
        self.lock = None
        self.stopped = False
        self.thread_limit = 0
        self.first_subdomain_found = False
        self.subdomains_found = 0
        self.subdomain_found_message = None
        self.executor = None
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments):
        """
        Custom validation method to validate the ipinfo command arguments.
        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        """
        self.domain = user_arguments[0]
        self.file = user_arguments[1]
        if not os.path.exists(self.file):
            console.print(Msg.get('errors.invalidFile'))
            return False
        if not Validator.is_domain(domain=self.domain):
            console.print(Msg.get('errors.invalidDomain'))
            return False
        return True

    def run(self, arguments, authentication: Authentication) -> bool:
        """
        Run the server command.
        :param arguments: list: The arguments to run the command
        :param authentication: Authentication: Auth object
        :return: bool: True if the command was executed successfully, False otherwise
        """
        if not self.validate_arguments(arguments):
            return False
        
        self.logs_manager = LogsManager(command_name=self.name)
        self.subdomain_found_message = Msg.get(f"commands.{self.name}.messages.subdomainFound")
        self.subdomains_found = 0
        self.first_subdomain_found = False
        self.stopped = False
        self.thread_limit = 300
        self.lock = Lock()
        self.executor = None

        subdomains = []
        with open(self.file, 'r') as f:
            subdomains = [line.strip() for line in f]

        if len(subdomains) == 0:
            console.print(Msg.get('errors.subdomainsFileEmpty'))
            return False

        console.print(Msg.get(f"commands.{self.name}.messages.wordlist").replace('%wordlist%', self.file).replace('%subdomains%', str(len(subdomains))))
        time.sleep(0.5)
        console.print(Msg.get(f"commands.{self.name}.messages.gettingSubdomains").replace('%domain%', self.domain))
        self.logs_manager.write(f"Getting subdomains for the domain: {self.domain}. Wordlist: {self.file}")

        thread_limit = min(len(subdomains), self.thread_limit)
        self.thread_limit = thread_limit

        text = Text()
        semaphore = BoundedSemaphore(thread_limit)
        with ThreadPoolExecutor(max_workers=thread_limit) as executor:
            self.executor = executor
            futures = [executor.submit(self._scan_subdomain, self.domain, subdomain, semaphore) for subdomain in subdomains]
            with Live(text, refresh_per_second=10, console=console) as live:
                animation = ['.', '..', '...']
                animation_index = 0
                try:
                    for future in as_completed(futures):
                        if self.stopped:
                            break
                        result = future.result()
                        if result:
                            subdomain, ip = result
                            if not self.first_subdomain_found:
                                self.first_subdomain_found = True
                                text.append(".", style="bold green")
                            text.append(".", style="bold green")
                            live.update(text)
                except KeyboardInterrupt:
                    self.stopped = True
                    console.print(Msg.get(f"commands.{self.name}.messages.stopped"))
                    self.executor.shutdown()
                    return True

        if self.subdomains_found == 0:
            console.print(f"No subdomains found for the domain: {self.domain}. Wordlist: {self.file}")
            return True

        console.print(Msg.get(f"commands.{self.name}.messages.subdomainsEnd").replace('%subdomains%', str(self.subdomains_found)).replace('%domain%', self.domain))
        self.logs_manager.write(f"{self.subdomains_found} subdomains found for the domain: {self.domain}. Wordlist: {self.file}")
        return True

    def _scan_subdomain(self, domain: str, subdomain: str, semaphore: BoundedSemaphore) -> Union[tuple, bool]:
        """
        Method to scan a subdomain.
        :param domain: str: The domain
        :param subdomain: str: The subdomain
        :param semaphore: BoundedSemaphore: Semaphore to limit the number of concurrent threads
        :return: Union[tuple, bool]: A tuple with subdomain and IP if found, otherwise False
        """
        with semaphore:
            if self.stopped:
                return False
            full_domain = f"{subdomain}.{domain}"
            try:
                ip = socket.gethostbyname(full_domain)
                with self.lock:
                    if self.stopped:
                        return False
                    self.subdomains_found += 1
                    console.print(self.subdomain_found_message.replace('%subdomain%', full_domain).replace('%ip%', ip))
                    if self.logs_manager:
                        self.logs_manager.write(f"Subdomain found: {full_domain} - IP: {ip}")
                    return full_domain, ip
            except (socket.gaierror, UnicodeError):
                return False