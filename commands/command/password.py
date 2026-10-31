from typing import Optional
import mccolors
from rich.console import Console
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg
from voidxtool.commands.validator import Validator
from voidxtool.commands.base import BaseCommand
from voidxtool.logs import LogsManager
from voidxtool.utilities.passwordsearch import PasswordSearch

console: Console = Console()

class PasswordCommand(BaseCommand):
    def __init__(self):
        super().__init__('password')
        self.logs_manager = None
        self.targets = []

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
        Custom validation method to validate the server command arguments.
        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        '''
        self.targets = user_arguments[:15]
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
        Run the server command.
        :param arguments: list: The arguments to run the command
        :param authentication: Authentication object
        :return: bool: True if the command was executed successfully, False otherwise
        '''
        if not self.validate_arguments(arguments):
            return False

        if authentication.plan == 'basic':
            console.print(Msg.get('onlyPro'))
            return False

        found_passwords = 0
        obfuscated_passwords = 0
        self.logs_manager = LogsManager(command_name=self.name)

        for username in self.targets:
            passwords = []
            obfuscated = []
            self.logs_manager.write(f'Sending request to api (username: {username})...')
            console.print(Msg.get(f'commands.{self.name}.messages.searching').replace('%username%', username))
            
            try:
                results = PasswordSearch.search(authentication=authentication, username=username)
                
                if len(results) == 0:
                    console.print(Msg.get(f'commands.{self.name}.messages.notFound').replace('%username%', username))
                    continue
                
                console.print(Msg.get(f'commands.{self.name}.messages.found').replace('%username%', username))
                
                for result in results:
                    if result.get('password'):
                        data = {
                            'serverName': result.get('servername', result.get('serverName')),
                            'serverip': result.get('serverip'),
                            'ip': result.get('ip'),
                            'password': result.get('password'),
                            'username': result.get('username')
                        }
                        
                        if len(data['password']) >= 32:
                            obfuscated.append(data)
                            obfuscated_passwords += 1
                        else:
                            found_passwords += 1
                            passwords.append(data)
                
                for password in passwords:
                    self._show_password(password)
                
                for password in obfuscated:
                    password['password'] = f"&c&l{password['password']}"
                    self._show_password(password)
                
                if found_passwords >= 1 or obfuscated_passwords >= 1:
                    console.print(
                        Msg.get(f'commands.{self.name}.messages.final')
                        .replace('%passwords%', str(found_passwords))
                        .replace('%obfuscated%', str(obfuscated_passwords))
                        .replace('%users%', str(len(self.targets)))
                    )
                    return True
            
            except Exception as e:
                console.print(Msg.get(f'commands.{self.name}.messages.notFound').replace('%username%', username))
                self.logs_manager.write(f'Error in password command! {e}')
        
        return True

    def _show_password(self, data: dict):
        '''
        Show the password result of the user.
        :param data: User data
        '''
        mccolors.mcwrite(
            Msg.get(f'commands.{self.name}.messages.data.serverName')
            .replace('%servername%', data.get('serverName', ''))
        )
        mccolors.mcwrite(
            Msg.get(f'commands.{self.name}.messages.data.serverip')
            .replace('%serverip%', data.get('serverip', ''))
        )
        mccolors.mcwrite(
            Msg.get(f'commands.{self.name}.messages.data.username')
            .replace('%username%', data.get('username', ''))
        )
        if data.get('ip'):
            mccolors.mcwrite(
                Msg.get(f'commands.{self.name}.messages.data.ip')
                .replace('%ip%', data.get('ip'))
            )
        mccolors.mcwrite(
            Msg.get(f'commands.{self.name}.messages.data.password')
            .replace('%password%', data.get('password', ''))
        )