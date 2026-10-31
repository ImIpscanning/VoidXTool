import psutil
import time
from typing import Optional
from rich.console import Console
from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand
from voidxtool.logs import LogsManager
from voidxtool.utilities.vulnserver.manager import VulnServerManager
from voidxtool.gui.language import Msg

console: Console = Console()

class VulnServerCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="vulnserver")
        self.logs_manager: Optional[LogsManager] = None
        self.server_name: str = ""

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        if len(user_arguments) < 1:
            console.print(Msg.get("errors.invalidArguments"))
            return False
        self.server_name = user_arguments[0]
        if self.server_name not in VulnServerManager.SERVER_NAMES:
            console.print(
                Msg.get("errors.invalidVulnerableServer").replace(
                    "%servers%", " ".join(VulnServerManager.SERVER_NAMES)
                )
            )
            return False
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        if not self.validate_arguments(arguments):
            return False

        server_manager = VulnServerManager(server_name=self.server_name)
        processes = server_manager.start()

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            console.print(Msg.get("ctrlC"))
            for pid in processes:
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    continue
            return True