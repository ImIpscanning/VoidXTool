import os.path as os
import re
from typing import Optional
from urllib.parse import urlsplit
from rich.console import Console
from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg
from voidxtool.utilities.pterodactyl.exploit import PterodactylTarget, PterodactylFinder

console: Console = Console()

class PterodactylCommand(BaseCommand):
    def __init__(self):
        super().__init__('pterodactyl')
        self.target = None
        self.new_targets = []
        self.file = None

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        '''
Custom validation method to validate the server command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
        self.target = user_arguments[0]
        self.new_targets = []

        if os.path.exists(self.target):
            self.file = self.target
            try:
                with open(self.target, 'r', encoding='utf-8') as f:
                    for line in f.readlines():
                        if Validator.is_ip_and_port(line):
                            ip, port = line.split(':')
                            self.new_targets.append(PterodactylTarget(ip=ip, port=port))
                        elif line.startswith(('http://', 'https://')):
                            hostname = urlsplit(line).hostname
                            self.new_targets.append(PterodactylTarget(domain=hostname))
                        else:
                            line = 'http://' + line
                            hostname = urlsplit(line).hostname
                            self.new_targets.append(PterodactylTarget(domain=hostname))
            except Exception as e:
                console.print(Msg.get('errors.invalidPterodactylExploitTargetFile'))
                return False
        elif ':' in self.target:
            match = re.search(r':(\d{2,5})(?:/|$)', self.target)
            if match and Validator.is_ip_address(self.target):
                ip = self.target
                port = match.group(1)
                self.target = f"{ip}:{port}"
            if Validator.is_ip_and_port(self.target):
                ip, port = self.target.split(':')
                self.new_targets.append(PterodactylTarget(ip=ip, port=port))
            else:
                console.print(Msg.get('errors.invalidPterodactylExploitTarget'))
                return False
        elif Validator.is_domain(self.target):
            self.new_targets.append(PterodactylTarget(domain=self.target))
        else:
            console.print(Msg.get('errors.invalidPterodactylExploitTarget'))
            return False

        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        '''
Run the pterodactyl command.

:param list arguments: The arguments to run the command
:param Authentication authentication: Auth object
:return bool: True if the command was executed successfully, False otherwise
'''
        if not self.validate_arguments(arguments):
            return False

        if len(self.new_targets) == 1:
            target = self.new_targets[0].domain or f"{self.new_targets[0].ip}:{self.new_targets[0].port}"
            console.print(Msg.get('commands.pterodactyl.messages.checkingSingleTarget').replace('%target%', target))
        else:
            console.print(
                Msg.get('commands.pterodactyl.messages.checkingMultiplesTarget')
                .replace('%file%', self.file)
                .replace('%targets%', str(len(self.new_targets)))
            )

        vulnerable_panels, targets_no_panel, vulnerable_panels_no_connection = PterodactylFinder(targets=self.new_targets).search()

        if vulnerable_panels == 0 and vulnerable_panels_no_connection == 0:
            console.print(
                Msg.get('commands.pterodactyl.messages.noPanelsFound')
                .replace('%targets%', str(targets_no_panel))
            )
        elif vulnerable_panels > 0 and vulnerable_panels_no_connection == 0:
            console.print(
                Msg.get('commands.pterodactyl.messages.vulnerablePanelsFoundNoSQL')
                .replace('%vulnerable%', str(vulnerable_panels))
                .replace('%targets%', str(targets_no_panel))
            )
        else:
            console.print(
                Msg.get('commands.pterodactyl.messages.vulnerablePanelsFound')
                .replace('%vulnerablePanels%', str(vulnerable_panels_no_connection))
                .replace('%vulnerablePanelsNoConnection%', str(vulnerable_panels))
                .replace('%targetsNoPanel%', str(targets_no_panel))
            )

        return True