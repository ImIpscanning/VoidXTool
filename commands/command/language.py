from typing import Optional
from rich.console import Console
from ezjsonpy import get_config_value, set_config_value, set_language
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.auth import Authentication
from voidxtool.gui.language import Msg

console = Console()

class LanguageCommand(BaseCommand):
    def __init__(self):
        super().__init__(name='language')
        self.language = None

    def custom_validate_arguments(self, user_arguments):
        '''
        Custom validation method to validate the language command arguments.
        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        '''
        self.language = user_arguments[0]
        if not Validator.is_valid_language(language=self.language):
            console.print(Msg.get('errors.invalidLanguage'))
            return False
        return True

    def run(self, arguments, authentication):
        '''
        Run the seeker command.
        :param arguments: list: The arguments to run the command
        :param authentication: Authentication: Auth object
        :return: bool: True if the command was executed successfully, False otherwise
        '''
        if not self.validate_arguments(arguments):
            return False

        current_language = get_config_value('language')
        if current_language == self.language:
            console.print(Msg.get(f'commands.{self.name}.messages.sameLanguage').replace('%language%', self.language))
            return False

        set_config_value('language', self.language)
        set_language(self.language)
        console.print(Msg.get(f'commands.{self.name}.messages.languageChanged').replace('%language%', self.language))
        return True