from typing import Optional
from rich.console import Console
from voidxtool.auth import Authentication
from voidxtool.utilities.velocity import StartProxy
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg

console: Console = Console()

class ProxyCommand(BaseCommand):
    def __init__(self):
        super().__init__('proxy')
        self.target = None
        self.velocity_forwarding_mode = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
        Custom validation method to validate the proxy command arguments.
        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        '''
        if len(user_arguments) < 2:
            console.print(Msg.get('errors.invalidArguments'))
            return False

        self.target = user_arguments[0]
        self.velocity_forwarding_mode = user_arguments[1]

        if not (Validator.is_domain(self.target) or 
                Validator.is_ip_and_port(ip=self.target) or 
                Validator.is_domain_and_port(domain=self.target)):
            console.print(Msg.get('errors.invalidServer'))
            return False

        if not Validator.is_velocity_forwarding_mode(self.velocity_forwarding_mode):
            console.print(
                Msg.get('errors.invalidVelocityForwardingMode')
                .replace('%mode%', self.velocity_forwarding_mode)
            )
            return False

        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
        Run the proxy command.
        :param arguments: list: The arguments to run the command
        :param authentication: Authentication object
        :return: bool: True if the command was executed successfully, False otherwise
        '''
        if not self.validate_arguments(arguments):
            return False

        try:
            StartProxy(server=self.target, forwarding_mode=self.velocity_forwarding_mode).start()
            return True
        except Exception as e:
            console.print(Msg.get('errors.proxyStartFailed').replace('%error%', str(e)))
            return False