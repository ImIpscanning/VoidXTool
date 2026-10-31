import datetime
import os
import subprocess
import threading
import time
import re
from ezjsonpy import get_config_value
from ezjsonpy.config_loader import Optional, Union
from rich.console import Console
from loguru import logger
from rstatus.models import JavaServerResponse, BedrockServerResponse
from voidxtool.utilities.velocity.jar import ProxyJarManager
from voidxtool.files import VoidXToolPath
from voidxtool.gui.language import Msg
from voidxtool.utilities.input import Input
from voidxtool.utilities.minecraft import ServerData
from voidxtool.utilities.notification import SendNotification
from voidxtool.utilities.pinggy import PinggyIOUtils
from voidxtool.utilities.tcp.port_checker import PortChecker

console: Console = Console()

class StartProxy:
    def __init__(self, server: str, forwarding_mode: str, fakeproxy: bool):
        self.server = server
        self.forwarding_mode = forwarding_mode
        self.fakeproxy = fakeproxy
        self.proxy_path = ''
        self.proxy_port = 0
        self.proxy_started = False
        self.update_thread = None
        self.stopped = False
        self.fakeproxy_pinggy_io_ip_and_port = None
        self.fakeproxy_update_mode = ''
        self.fakeproxy_protocol_mode = ''
        self.fakeproxy_command_prefix = ''
        self.fakeproxy_update_interval = 0

    def start(self):
        self.proxy_port = PortChecker.get_random()
        self._configure_proxy()
        process = self._start_proxy()
        self.proxy_started = True
        self.stopped = False
        if self.fakeproxy:
            self.update_thread = threading.Thread(target=self._fakeproxy_data_updater, daemon=True)
            self.update_thread.start()
        self._read_output(process)

    def _configure_proxy(self):
        console.print(Msg.get('commands.proxy.messages.configuringProxy'))
        data_path = VoidXToolPath.get_voidxtool_data_path()
        if self.fakeproxy:
            self.proxy_path = os.path.join(data_path, "fakeproxy.jar")
        else:
            self.proxy_path = os.path.join(data_path, "velocity.jar")

    def _read_output(self, process):
        try:
            while True:
                output = process.stdout.readline()
                if output == b'' and process.poll() is not None:
                    break
                if output:
                    text = output.decode('utf-8', errors='ignore').strip()
                    console.print(text)
        except Exception as e:
            logger.error(f"Error reading proxy output: {e}")

    @staticmethod
    def minimessage_colors(text: str) -> str:
        color_pattern = re.compile(r'<([a-zA-Z]+)>')
        return color_pattern.sub('', text)

    def _fakeproxy_data_updater(self):
        while not self.stopped:
            time.sleep(self.fakeproxy_update_interval or 5)

    def _start_proxy(self):
        console.print(Msg.get('commands.proxy.messages.startingProxy'))
        jar_name = 'fakeproxy' if self.fakeproxy else 'velocity'
        ProxyJarManager(jar_name=jar_name, jar_path=self.proxy_path).check()
        cmd = [
            "java",
            "-jar",
            self.proxy_path,
            "--port",
            str(self.proxy_port)
        ]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1
        )
        return process