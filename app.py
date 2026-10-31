import subprocess
import threading
import time
import sys
import os
from typing import Union
from loguru import logger
from rich.console import Console
from ezjsonpy import load_language, load_configuration, get_config_value, set_language
from voidxtool.api.settings import APISettings
from voidxtool.files import LocalFilesChecker, VoidXToolPath
from voidxtool.gui import VoidXToolGUI
from voidxtool.auth import Authentication
from voidxtool.constants import VoidXToolConstants
from voidxtool.gui.banners import VoidXToolBanner
from voidxtool.files import WindowsInstaller
from voidxtool.utilities.input import Input
from voidxtool.updater import UpdaterCheck
from voidxtool.api.api import VoidXToolInternalAPI
from voidxtool.utilities.tcp.port_checker import PortChecker
from voidxtool.security.manager import SecurityManager

console = Console()
logger.add(sys.stdout, colorize=True, format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>')
logger.remove()
logger.add(os.path.join(VoidXToolPath.get_voidxtool_data_path(), 'logs.log'), level='DEBUG', format='[{time} {level} - {file}, {line}] ⮞ <level>{message}</level>', rotation='30 MB')
APISettings()

class VoidXTool:
    def __init__(self):
        self.skip_nodejs = False
        self.skip_installer = False
        
        if '--update' in sys.argv[1:]:
            WindowsInstaller().update()
            sys.exit(0)
            
        if '--skip-nodejs' in sys.argv:
            self.skip_nodejs = True
            
        if '--skip-installer' in sys.argv:
            self.skip_installer = True
            
        self._files_check()
        self._load()

        if '--install' in sys.argv[1:] and not self.skip_installer:
            self._installer()

        if '--check-update' in sys.argv[1:]:
            self._update_check()
        if '--security-check' in sys.argv[1:]:
            SecurityManager()
        self.auth = Authentication()
        
        if not self.auth.login():
            console.print('\n\n[red1]Exiting VoidXTool...')
            time.sleep(2)
            sys.exit(0)
            
        try:
            self.run()
        except KeyboardInterrupt:
            console.print('\n\n[red1]Exiting VoidXTool...')
            time.sleep(2)
            sys.exit(0)

    def _files_check(self):
        """Check if the VoidXTool files are present

        :return bool: True if the files are present, False otherwise
        """
        checker = LocalFilesChecker()
        checker.create_settings_file()
        return True

    @staticmethod
    def _update_check():
        """Check if an update is available"""
        if not UpdaterCheck.update_available():
            return
            
        if os.name == 'nt':
            logger.info('An update is available')
            WindowsInstaller().update()
        else:
            console.print(f"{VoidXToolConstants.INFO_PREFIX} [bright white]An update is available. Go to the VoidXTool website to download it. (Linux update not implemented yet)")
            time.sleep(5)
            sys.exit(0)

    def _load(self):
        """Load VoidXTool settings and language"""
        try:
            load_configuration(config_name='default', config_path=os.path.join(VoidXToolPath.get_voidxtool_data_path(), 'settings.json'))
            
            for lang in VoidXToolConstants.LANGUAGES:
                language_path = os.path.join(VoidXToolPath.get_voidxtool_data_path(), 'languages', f'{lang}.json')
                if os.path.exists(language_path):
                    load_language(lang, language_path)

            set_language(str(get_config_value('language', 'en')))
                
        except ValueError:
            logger.error('Error loading the settings file. (Invalid JSON format)')
            logger.info('Creating a new settings file')
            LocalFilesChecker().create_settings_file()
            self._load()

    @staticmethod
    def _installer():
        """Run VoidXTool installer"""
        if os.path.exists(VoidXToolPath.get_voidxtool_installed_path()) or os.path.exists(os.path.join(VoidXToolPath.get_voidxtool_data_path(), 'portable.voidxtool')):
            return
            
        subprocess.run('clear || cls', shell=True)
        VoidXToolBanner.show_install_banner()
        
        user_input = Input.get_input(
            input_message=f"{VoidXToolConstants.SPACES}{VoidXToolConstants.INPUT_PREFIX} Do you want to install VoidXTool? [Y/n]",
            input_type='boolean'
        )
        print()
        
        if user_input is None:
            return
            
        if not user_input:
            with open(os.path.join(VoidXToolPath.get_voidxtool_data_path(), 'portable.voidxtool'), 'w') as f:
                f.write(' ')
            return
            
        if os.name == 'nt':
            WindowsInstaller().install()

    def run(self):
        """Run VoidXTool"""
        if os.name == 'nt':
            subprocess.run(f'title VoidXTool v{VoidXToolConstants.VERSION}', shell=True)
            
        if PortChecker.check(int(get_config_value('api.port'))):
            logger.info('The voidxtool API port is already in use!')
            
        if get_config_value('api.enabled'):
            if self.auth.plan != 'basic':
                api_thread = threading.Thread(
                    target=VoidXToolInternalAPI(authentication=self.auth, port=int(get_config_value('api.port'))).run,
                    daemon=True
                )
                api_thread.start()
                
        VoidXToolGUI(authentication=self.auth).menu()
