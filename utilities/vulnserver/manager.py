import os
import subprocess
import time
from subprocess import Popen
from typing import Optional, List
import psutil
import requests
from ezjsonpy import get_config_value
from rich.console import Console
from loguru import logger
from voidxtool.files import VoidXToolPath
from voidxtool.gui.language import Msg

console: Console = Console()

class VulnServerManager:
    HOLOGRAPHIC_DISPLAYS: str = 'holographicdisplays'
    AUTHMEVELOCITY: str = 'authmevelocity'
    EASYCOMMANDBLOCKER: str = 'easycommandblocker'
    CMDPANELS_PAPI: str = 'cmdpanelspapi'
    PLUGIN_MANAGER: str = 'pluginmanager'
    PLUGMAN_X: str = 'plugmanx'
    CLOUDSYNC: str = 'cloudsync'
    MULTICHAT: str = 'multichat'
    SIGNEDVELOCITY: str = 'signedvelocity'
    T2C: str = 't2c'
    PAPER_1_8_BACKEND: str = 'Paper-1.8.8'
    PAPER_1_21_4_BACKEND: str = 'Paper-1.21.4'
    WATERFALL_1_21_BACKEND: str = 'Waterfall-1.8.8'
    VELOCITY_3_4_0: str = 'Velocity_3_4_0'
    JAR_DOWNLOADS_ENDPOINTS: dict = {
        VELOCITY_3_4_0: 'https://api.papermc.io/v2/projects/velocity/versions/3.4.0-SNAPSHOT/builds/496/downloads/velocity-3.4.0-SNAPSHOT-496.jar',
        WATERFALL_1_21_BACKEND: 'https://api.papermc.io/v2/projects/waterfall/versions/1.21/builds/584/downloads/waterfall-1.21-584.jar',
        PAPER_1_21_4_BACKEND: 'https://api.papermc.io/v2/projects/paper/versions/1.21.4/builds/226/downloads/paper-1.21.4-226.jar',
        PAPER_1_8_BACKEND: 'https://api.papermc.io/v2/projects/paper/versions/1.8.8/builds/445/downloads/paper-1.8.8-445.jar'
    }
    SERVER_NAMES: List[str] = [
        HOLOGRAPHIC_DISPLAYS,
        AUTHMEVELOCITY,
        EASYCOMMANDBLOCKER,
        CMDPANELS_PAPI,
        PLUGIN_MANAGER,
        PLUGMAN_X,
        MULTICHAT,
        SIGNEDVELOCITY,
        T2C
    ]
