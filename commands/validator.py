import socket
from rich.console import Console
from ezjsonpy import get_languages
from voidxtool.gui.language import Msg

console: Console = Console()

class Validator:
    __firstlineno__ = 11

    @staticmethod
    def validate_arguments_length(command_name: str, command_arguments: list, user_arguments: list) -> bool:
        '''
        Method to validate the length of the arguments
        :param command_name: The name of the command
        :param command_arguments: Command arguments
        :param user_arguments: User arguments
        :return: True if the arguments are valid, False otherwise
        '''
        try:
            for i in range(len(command_arguments)):
                _ = user_arguments[i]
            return True
        except IndexError:
            missing_args_msg = Msg.get("errors.missingArguments")
            args_str = ""
            for arg in command_arguments[len(user_arguments):]:
                args_str += f"[green1]{arg} [/green1]"
            for arg in command_arguments[:len(user_arguments)]:
                args_str += f"[red1]{arg}[/red1] "
            missing_args_msg = missing_args_msg.replace("%command%", command_name)
            missing_args_msg = missing_args_msg.replace("%arguments%", args_str)
            console.print(missing_args_msg)
            return False

    @staticmethod
    def is_domain(domain: str, allow_connection_error=False) -> bool:
        '''
        Method to validate if a string is a domain
        :param domain: The domain
        :return: True if the domain is valid, False otherwise
        '''
        if Validator.is_ip_address(domain):
            return False
        if '.' not in domain:
            return False
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            if allow_connection_error:
                return True
            return False

    @staticmethod
    def is_domain_and_port(domain: str) -> bool:
        '''
        Method to validate if a string is a domain and port
        :param domain: The domain and port
        :return: True if the domain and port is valid, False otherwise
        '''
        if ':' not in domain:
            return False
        parts = domain.split(':')
        if len(parts) != 2:
            return False
        domain_part = parts[0]
        port_part = parts[1]
        if not domain_part or not port_part:
            return False
        if not Validator.is_domain(domain_part):
            return False
        try:
            port = int(port_part)
            if port < 0 or port > 65535:
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def is_ip_address(ip: str) -> bool:
        '''
        Method to validate if a string is an IP address
        :param ip: The IP address
        :return: True if the IP address is valid, False otherwise
        '''
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except (AttributeError, ValueError):
            return False

    @staticmethod
    def is_ip_and_port(ip: str) -> bool:
        '''
        Method to validate if a string is an IP and port
        :param ip: The IP and port
        :return: True if the IP and port is valid, False otherwise
        '''
        if ':' not in ip:
            return False
        parts = ip.split(':')
        if len(parts) != 2:
            return False
        ip_part = parts[0]
        port_part = parts[1]
        if not ip_part or not port_part:
            return False
        try:
            port = int(port_part)
            if port < 0 or port > 65535:
                return False
            ip_parts = ip_part.split('.')
            if len(ip_parts) != 4:
                return False
            for part in ip_parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except ValueError:
            return False

    @staticmethod
    def is_port(port: str) -> bool:
        '''
        Method to validate if a string is a port
        :param port: The port
        :return: True if the port is valid, False otherwise
        '''
        if not port.isnumeric():
            return False
        try:
            port_num = int(port)
            if port_num < 0 or port_num > 65535:
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def is_port_range_py_method(port_range: str) -> bool:
        '''
        Method to validate if a string is a port range for the py method
        :param port_range: The port range
        :return: True if the port range is valid, False otherwise
        '''
        if '-' not in port_range:
            if not port_range.isnumeric():
                return False
            try:
                port_num = int(port_range)
                if port_num < 0 or port_num > 65535:
                    return False
                return True
            except ValueError:
                return False
        try:
            start, end = port_range.split('-')
            start = int(start)
            end = int(end)
            if start < 0 or start > 65535 or end < 0 or end > 65535:
                return False
            if start > end:
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def is_scan_method(method: str) -> bool:
        '''
        Method to validate if a string is a scanner method
        :param method: The scanner method
        :return: True if the scanner method is valid, False otherwise
        '''
        return method in ('nmap', 'old_qubo', 'qubo', 'masscan', 'rustscan')

    @staticmethod
    def is_yes_no(value: str) -> bool:
        '''
        Method to validate if a string is a yes or no value
        :param value: The value
        :return: True if the value is valid, False otherwise
        '''
        return value in ('y', 'n')

    @staticmethod
    def is_proxy_type(proxy_type: str) -> bool:
        '''
        Method to validate if a string is a proxy type
        :param proxy_type: The proxy type
        :return: True if the proxy type is valid, False otherwise
        '''
        return proxy_type in ('waterfall', 'velocity')

    @staticmethod
    def is_velocity_forwading_mode(mode: str) -> bool:
        '''
        Method to validate if a string is a velocity forwarding mode
        :param mode: The velocity forwarding mode
        :return: True if the velocity forwarding mode is valid, False otherwise
        '''
        return mode in ('none', 'legacy', 'bungeeguard', 'modern')

    @staticmethod
    def is_fakeproxy_update_mode(mode: str) -> bool:
        '''
        Method to validate if a string is a fakeproxy update mode
        :param mode: The fakeproxy update_mode
        :return: True if the fakerpoxy update mode is valid, False otherwise
        '''
        return mode in ('1', '2')

    @staticmethod
    def is_fakeproxy_protocol_mode(mode: str) -> bool:
        '''
        Method to validate if a string is a fakeproxy protocol mode
        :param mode: The fakeproxy protocol mode
        :return: True if the fakerpoxy protocol mode is valid, False otherwise
        '''
        return mode in ('1', '2')

    @staticmethod
    def is_valid_language(language: str) -> bool:
        '''
        Method to validate if a string is a valid language
        :param language: The language
        :return: True if the language is valid, False otherwise
        '''
        return language in get_languages()

    @staticmethod
    def is_valid_customport_option(option: str) -> bool:
        '''
        Method to validate if a string is a valid customport option
        :param option: The webhook option
        :return: True if the webhook option is valid, False otherwise
        '''
        return option in ('add', 'remove', 'list')

    @staticmethod
    def is_valid_webhook_option(option: str) -> bool:
        '''
        Method to validate if a string is a valid webhook option
        :param option: The webhook option
        :return: True if the webhook option is valid, False otherwise
        '''
        return option in ('add', 'remove', 'list')

    @staticmethod
    def is_valid_serverdata_mode(mode: str) -> bool:
        '''
        Method to validate if a string is a valid serverdata mode
        :param mode: The serverdata mode
        :return: True if the serverdata mode is valid, False otherwise
        '''
        return mode in ('local', 'mcstatus.io')

    @staticmethod
    def is_valid_randomservers_minimum(minimum: str) -> bool:
        '''
        Method to validate if a string is a valid minimum server count for the randomservers command.

        :param minimum: Minimum number as a string
        :return: True if the minimum is a valid integer >= 1, False otherwise
        '''
        try:
            return int(minimum) >= 1
        except ValueError:
            return False

    __static_attributes__ = ()