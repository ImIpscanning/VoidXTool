import os
import requests
from ezjsonpy import get_config_value, set_config_value
from loguru import logger
from rich.console import Console
from voidxtool.files import VoidXToolPath
from voidxtool.gui.language import Msg

console: Console = Console()

class ProxyJarManager:
    __firstlineno__ = 14

    def __init__(self, jar_name: str, jar_path: str):
        self.jar_name = jar_name
        self.jar_path = jar_path

    def check(self):
        if not os.path.exists(self.jar_path):
            logger.error(f'Jar file not found: {self.jar_path}. Downloading it')
            self._download()
        else:
            self._get_latest_version()

    def _get_latest_version(self):
        try:
            url = self._get_download_url()
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                versions = data.get('versions', [])
                if versions:
                    latest_version = versions[-1]
                    console.print(Msg.get('commands.proxy.messages.newVelocityVersionAvailable').replace('%version%', latest_version))
                    return latest_version
            return None
        except Exception as e:
            logger.error(f'Error while getting the latest version of the jar file -> {e}')
            return None

    @staticmethod
    def _get_download_url() -> str:
        return 'https://api.papermc.io/v2/projects/velocity'

    def _download(self) -> bool:
        try:
            console.print(Msg.get('commands.proxy.messages.downloadingJar').replace('%jarName%', self.jar_name))
            data_path = VoidXToolPath.get_voidxtool_data_path()
            latest_version = self._get_latest_version()
            if not latest_version:
                return False
            download_url = f'https://api.papermc.io/v2/projects/velocity/versions/{latest_version}/builds/latest/downloads/{self.jar_name}.jar'
            jar_file_path = os.path.join(data_path, f'{self.jar_name}.jar')
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                with open(jar_file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            return False
        except Exception as e:
            logger.error(f'Error downloading jar: {e}')
            return False

    def _replace_jar(self) -> bool:
        try:
            console.print(Msg.get('commands.proxy.messages.replacingJar'))
            if os.path.exists(self.jar_path):
                os.remove(self.jar_path)
            data_path = VoidXToolPath.get_voidxtool_data_path()
            new_jar_path = os.path.join(data_path, f'{self.jar_name}.jar')
            if os.path.exists(new_jar_path):
                os.rename(new_jar_path, self.jar_path)
                return True
            return False
        except Exception as e:
            logger.error(f'Error replacing jar: {e}')
            return False