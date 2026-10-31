import subprocess
import zipfile
import shutil
import time
import sys
import os
from dataclasses import dataclass
from typing import Optional, List
import requests
from ezjsonpy import get_config_value
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TaskID
from loguru import logger
from voidxtool.files.path import VoidXToolPath
from voidxtool.constants import VoidXToolConstants, UrlConstants

console: Console = Console()

@dataclass
class VoidXToolFile:
    name: str
    path: str
    size: Optional[int] = None
DATA_FOLDER = VoidXToolPath.get_voidxtool_data_path()
class VoidXToolFiles:
    def __init__(self):
        self.files = [
            VoidXToolFile(name='settings.json', path=os.path.join(DATA_FOLDER, 'settings.json')),
            VoidXToolFile(name='languages/en.json', path=os.path.join(DATA_FOLDER, 'languages/en.json')),
            VoidXToolFile(name='languages/es.json', path=os.path.join(DATA_FOLDER, 'languages/es.json')),
            VoidXToolFile(name='languages/ru.json', path=os.path.join(DATA_FOLDER, 'languages/ru.json')),
            VoidXToolFile(name='languages/ur.json', path=os.path.join(DATA_FOLDER, 'languages/ur.json')),
            VoidXToolFile(name='languages/fr.json', path=os.path.join(DATA_FOLDER, 'languages/fr.json')),
            VoidXToolFile(name='languages/fa.json', path=os.path.join(DATA_FOLDER, 'languages/fa.json')),
            VoidXToolFile(name='languages/de.json', path=os.path.join(DATA_FOLDER, 'languages/de.json')),
            VoidXToolFile(name='languages/pt.json', path=os.path.join(DATA_FOLDER, 'languages/pt.json')),
            VoidXToolFile(name='languages/ja.json', path=os.path.join(DATA_FOLDER, 'languages/ja.json')),
            VoidXToolFile(name='scanners/old_qubo.jar', path=os.path.join(DATA_FOLDER, 'scanners/old_qubo.jar')),
            VoidXToolFile(name='scanners/qubo.jar', path=os.path.join(DATA_FOLDER, 'scanners/qubo.jar')),
            VoidXToolFile(name='scanners/masscan', path=os.path.join(DATA_FOLDER, 'scanners/masscan')),
            VoidXToolFile(name='scanners/rustscan', path=os.path.join(DATA_FOLDER, 'scanners/rustscan')),
            VoidXToolFile(name='scanners/rustscan.exe', path=os.path.join(DATA_FOLDER, 'scanners/rustscan.exe')),
            VoidXToolFile(name='velocity.toml', path=os.path.join(DATA_FOLDER, 'velocity.toml')),
            VoidXToolFile(name='mcserver-scrapper.json', path=os.path.join(DATA_FOLDER, 'mcserver-scrapper.json')),
            VoidXToolFile(name='config.yml', path=os.path.join(DATA_FOLDER, 'config.yml')),
            VoidXToolFile(name='vulnservers', path=os.path.join(DATA_FOLDER, 'vulnservers')),
            VoidXToolFile(name='proxies/fakeproxy/plugins/RFakeProxy.jar', path=os.path.join(DATA_FOLDER, 'proxies/fakeproxy/plugins/RFakeProxy.jar')),
            VoidXToolFile(name='proxies/velocity/plugins/VoidXToolVelocity.jar', path=os.path.join(DATA_FOLDER, 'proxies/velocity/plugins/VoidXToolVelocity.jar')),
            VoidXToolFile(name='voidxtoolbot.json', path=os.path.join(DATA_FOLDER, 'voidxtoolbot.json')),
            VoidXToolFile(name='voidxtoolBot.js', path=os.path.join(DATA_FOLDER, 'voidxtoolBot.js')),
            VoidXToolFile(name='response.mjs', path=os.path.join(DATA_FOLDER, 'response.mjs')),
            VoidXToolFile(name='connect.mjs', path=os.path.join(DATA_FOLDER, 'connect.mjs')),
            VoidXToolFile(name='kick.mjs', path=os.path.join(DATA_FOLDER, 'kick.mjs')),
            VoidXToolFile(name='botter.mjs', path=os.path.join(DATA_FOLDER, 'botter.mjs')),
            VoidXToolFile(name='utils.mjs', path=os.path.join(DATA_FOLDER, 'utils.mjs')),
            VoidXToolFile(name='package.json', path=os.path.join(DATA_FOLDER, 'package.json')),
            VoidXToolFile(name='icon.ico', path=os.path.join(DATA_FOLDER, 'icon.ico')),
        ]

    def get_files(self) -> List[VoidXToolFile]:
        '''
Get the list of VoidXTool files.

:return list[VoidXToolFile]: The list of VoidXTool files.
'''
        return self.files

    def get_voidxtool_file_list(self) -> List[str]:
        '''
Get the list of VoidXTool files.

:return list[str]: The list of VoidXTool files.
'''
        return [
            'settings.json',
            'languages/en.json',
            'languages/es.json',
            'languages/ru.json',
            'languages/ur.json',
            'languages/fr.json',
            'languages/fa.json',
            'languages/de.json',
            'languages/pt.json',
            'languages/ja.json',
            'scanners/old_qubo.jar',
            'scanners/qubo.jar',
            'scanners/masscan',
            'scanners/rustscan',
            'scanners/rustscan.exe',
            'velocity.toml',
            'mcserver-scrapper.json',
            'config.yml',
            'vulnservers',
            'proxies/fakeproxy/plugins/RFakeProxy.jar',
            'proxies/velocity/plugins/VoidXToolVelocity.jar',
            'voidxtoolbot.json',
            'voidxtoolBot.js',
            'response.mjs',
            'connect.mjs',
            'kick.mjs',
            'botter.mjs',
            'utils.mjs',
            'package.json',
            'icon.ico'
        ]

class LocalFilesChecker:
    def __init__(self):
        self.files = VoidXToolFiles().get_files()

    def check(self, skip_nodejs: bool) -> bool:
        '''
Check if the local files are present.

:return bool: True if the local files are present, False otherwise.
'''
        missing_files = []
        for file in self.files:
            if not os.path.exists(file.path):
                missing_files.append(file.name)
        if missing_files:
            logger.error(f"Missing files: {missing_files}")
            return False
        if not skip_nodejs:
            nodejs_path = shutil.which("node")
            if nodejs_path is None:
                logger.error("Node.js is not installed or not found in PATH.")
                return False
        return True

    def restore(self):
        '''Restore the local files '''
        if not UrlConstants.VOIDXTOOL_FILES_URL:
            logger.error(
                "Asset restore is not configured. Set VOIDXTOOL_API_BASE_URL "
                "to an owner-controlled backend or install reviewed assets manually."
            )
            return
        for file in self.files:
            if not os.path.exists(file.path):
                url = UrlConstants.VOIDXTOOL_FILES_URL + file.name
                try:
                    response = requests.get(url, stream=True, timeout=15)
                    response.raise_for_status()
                    os.makedirs(os.path.dirname(file.path), exist_ok=True)
                    with open(file.path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logger.info(f"Restored {file.name}")
                except Exception as e:
                    logger.error(f"Failed to restore {file.name}: {e}")

    def create_settings_file(self):
        '''
Create the settings file when the actual file is invalid.
'''
        settings_path = os.path.join(DATA_FOLDER, 'settings.json')
        if os.path.exists(settings_path):
            return
        default_settings = {
            "language": "en",
            "theme": "dark",
            "auto_update": False,
            "debug": False,
            "discordPresence": False,
            "serverStatusGetMode": "local",
            "serverShowMode": "default",
            "api": {"enabled": False, "port": 8765},
            "customports": [],
            "webhooks": [],
            "nmapCommand": "nmap",
            "masscanCommand": "masscan"
        }
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, "w") as f:
            import json
            json.dump(default_settings, f, indent=4)
        logger.info("Created default settings.json")

    def _extract_zip(self, file: str):
        '''Extract the zip file '''
        if not zipfile.is_zipfile(file):
            logger.error(f"{file} is not a valid zip file.")
            return
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(DATA_FOLDER)
        logger.info(f"Extracted {file} to {DATA_FOLDER}")
