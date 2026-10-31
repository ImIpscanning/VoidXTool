from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from loguru import logger
from voidxtool.auth import Authentication
from voidxtool.logs import LogsManager
from voidxtool.utilities.rcon import MCRcon, MCRconException
from voidxtool.constants import VoidXToolConstants
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg

console: Console = Console()

class RconCommand(BaseCommand):
    def __init__(self):
        super().__init__('rcon')
        self.target = None
        self.password = None
        self.ip_address = None
        self.port = None
        self.mcr = None
        self.first_command = True
        self.logs_manager = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
Custom validation method to validate the rcon command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.target = user_arguments[0]
        self.password = user_arguments[1]
        if not Validator.is_ip_and_port(self.target):
            console.print(Msg.get('errors.invalidIpAndPort'))
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
Run the rcon command.

:param arguments: list: The arguments to run the command
:param authentication: Authentication: Auth object
:return: bool: True if the command was executed successfully, False otherwise
'''
        if not self.validate_arguments(arguments):
            return False

        self.ip_address = self.target.split(':')[0]
        self.port = self.target.split(':')[1]
        self.mcr = None
        self.first_command = True
        self.logs_manager = LogsManager(command_name=self.name)
        self._connect()
        return True

    def _connect(self):
        '''
Establish an RCON connection and handle command input.
'''
        console.print(
            Msg.get(f'commands.{self.name}.messages.connecting')
            .replace('%server%', f'{self.ip_address}:{self.port}')
        )
        self.logs_manager.write(f'Connecting to {self.ip_address}:{self.port}...')
        
        try:
            with MCRcon(
                host=self.ip_address,
                password=self.password,
                port=int(self.port),
                timeout=10
            ) as mcr:
                self.mcr = mcr
                console.print(Msg.get(f'commands.{self.name}.messages.connected'))
                
                while True:
                    command = Prompt.ask(Msg.get(f'commands.{self.name}.messages.commandInput'))
                    if command == '.exit':
                        console.print(Msg.get(f'commands.{self.name}.messages.disconnected'))
                        if self.mcr:
                            self.mcr.disconnect()
                        break
                    
                    response = self.mcr.command(command)
                    console.print(f'\n{VoidXToolConstants.SPACES}{response}')
                
        except TimeoutError:
            console.print(Msg.get('errors.rconTimeout'))
        except ConnectionRefusedError:
            console.print(Msg.get('errors.rconConnectionRefused'))
        except MCRconException:
            console.print(Msg.get('errors.rconInvalidPassword'))
        except KeyboardInterrupt:
            if self.mcr:
                self.mcr.disconnect()
            console.print(Msg.get(f'commands.{self.name}.messages.disconnected'))
        except Exception as e:
            console.print(Msg.get('errors.rconUnknownError'))
            logger.error(f'Error in rcon command: {e}')
            self.logs_manager.write(f'Error in rcon command! {e}')