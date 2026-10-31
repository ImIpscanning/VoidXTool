import os
import subprocess
import json
import shutil
from rich.console import Console
from ezjsonpy import load_configuration, remove_configuration
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.files.local_files import VoidXToolPath
from voidxtool.gui.language import Msg

console: Console = Console()

class SettingsCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="settings")

    def custom_validate_arguments(self, user_arguments):
        '''
Custom validation method to validate the settings command arguments.
:param user_arguments: list: The arguments to validate
:return: bool: True if the arguments are valid, False otherwise
'''
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
        settings_path = os.path.join(VoidXToolPath.get_voidxtool_data_path(), "settings.json")
        default_config = "default"
        editor = os.getenv("VISUAL") or os.getenv("EDITOR")
        if not editor:
            editor = "notepad" if os.name == "nt" else (shutil.which("nano") or shutil.which("vi"))
        if not editor:
            console.print(f"[yellow]No text editor was found. Settings:[/yellow] {settings_path}")
            return False
        try:
            with open(settings_path, 'r', encoding='utf-8') as file:
                old_config = file.read()
            subprocess.run([editor, settings_path], check=False)
            with open(settings_path, 'r', encoding='utf-8') as file:
                new_config = file.read()
            json.loads(new_config)
            remove_configuration(default_config)
            load_configuration(default_config, settings_path)
            console.print(Msg.get(f"commands.{self.name}.messages.settingsUpdated"))
            return True
        except json.JSONDecodeError:
            console.print(Msg.get('errors.invalidNewSettingsFile'))
            with open(settings_path, 'w', encoding='utf-8') as file:
                file.write(old_config)
            return True
        except OSError as exc:
            console.print(f"[red]Could not open settings:[/red] {exc}")
            return False
