import os
from typing import Union, Optional
from rich.console import Console
from rich.prompt import Prompt
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg

console: Console = Console()

class Input:
    __firstlineno__ = 13

    def __init__(self, input_message: str, input_type: str):
        '''
        Initialize the Input class
        :param input_message: str: The custom input message
        :param input_type: str: The custom input type
        '''
        self.input_message = input_message
        self.input_type = input_type
        self.user_input = ''

    def get_input(self) -> Union[str, int, bool, None]:
        '''
        Method to get the user input and validate it
        :return: Value of the user input or None if the input is invalid
        '''
        self.user_input = Prompt.ask(self.input_message)
        if self.input_type == "string":
            return self._string_input()
        elif self.input_type == "int":
            return self._integer_input()
        elif self.input_type == "bool":
            return self._boolean_input()
        elif self.input_type == "country_code":
            return self._country_code_input()
        elif self.input_type == "velocity_forwarding_mode":
            return self._velocity_forwarding_mode_input()
        elif self.input_type == "fakeproxy_update_mode":
            return self._fakeproxy_update_mode_input()
        elif self.input_type == "fakeproxy_protocol_mode":
            return self._fakeproxy_protocol_mode_input()
        elif self.input_type == "proxy":
            return self._proxy_input()
        elif self.input_type == "file_path":
            return self._file_path()
        else:
            return self.user_input

    def _string_input(self) -> str:
        '''Get the string input'''
        return self.user_input

    def _integer_input(self) -> Optional[int]:
        '''Get the integer input'''
        try:
            return int(self.user_input)
        except ValueError:
            console.print(Msg.get('errors.invalidIntegerInput'))
            return None

    def _boolean_input(self) -> Optional[bool]:
        '''Get the boolean input'''
        val = self.user_input.lower()
        if val in ('yes', 'y', 'true', 'si', 's'):
            return True
        elif val in ('no', 'n', 'false'):
            return False
        else:
            console.print(Msg.get('errors.invalidBooleanInput'))
            return None

    def _country_code_input(self) -> Optional[str]:
        '''Get the country code input'''
        if len(self.user_input) == 2:
            return self.user_input.upper()
        else:
            console.print(Msg.get('errors.invalidCountryCodeInput'))
            return None

    def _velocity_forwarding_mode_input(self) -> Optional[str]:
        '''Get the velocity forwarding mode input'''
        if Validator.is_velocity_forwading_mode(self.user_input):
            return self.user_input
        else:
            console.print(Msg.get('errors.invalidVelocityForwardingModeInput'))
            return None

    def _fakeproxy_update_mode_input(self) -> Optional[str]:
        '''Get the fakeproxy update mode input'''
        if Validator.is_fakeproxy_update_mode(self.user_input):
            return self.user_input
        else:
            console.print(Msg.get('errors.invalidFakeProxyUpdateModeInput'))
            return None

    def _fakeproxy_protocol_mode_input(self) -> Optional[str]:
        '''Get the fakeproxy protocol mode input'''
        if Validator.is_fakeproxy_protocol_mode(self.user_input):
            return self.user_input
        else:
            console.print(Msg.get('errors.invalidFakeProxyProtocolModeInput'))
            return None

    def _proxy_input(self) -> Optional[str]:
        '''Get the proxy input'''
        if Validator.is_ip_and_port(self.user_input):
            return self.user_input
        else:
            console.print(Msg.get('errors.invalidProxyInput'))
            return None

    def _file_path(self) -> Optional[str]:
        '''Get the file path input'''
        if os.path.exists(self.user_input):
            return self.user_input
        else:
            console.print(Msg.get('errors.invalidFilePath'))
            return None

    __static_attributes__ = ('input_message', 'input_type', 'user_input')