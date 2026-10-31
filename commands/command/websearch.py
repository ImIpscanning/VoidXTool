import threading
import time
from typing import Union, Optional
from rich.console import Console
from voidxtool.gui.language import Msg
from voidxtool.commands.base import BaseCommand
from voidxtool.logs import LogsManager
from voidxtool.utilities.input import Input
from voidxtool.utilities.scrapper import MinecraftServerScrapper
from voidxtool.utilities.minecraft import GetServersData, ServersFound

console: Console = Console()

class WebSearchCommand(BaseCommand):
    def __init__(self):
        super().__init__(name="websearch")
        self.logs_manager: Optional[LogsManager] = None

    def run(self, arguments: list) -> bool:
        self.logs_manager = LogsManager(command_name=self.name)
        scrapper = MinecraftServerScrapper(logs_manager=self.logs_manager)
        if scrapper.servers == {}:
            console.print(
                Msg.get(f"commands.{self.name}.messages.failedToLoadConfigurationFile")
            )
            if self.logs_manager:
                self.logs_manager.write(
                    "\nFailed to load the Minecraft server scrapper configuration file"
                )
            return False

        thread = threading.Thread(target=scrapper.get)
        thread.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            scrapper.stop()
            console.print(Msg.get(f"commands.{self.name}.messages.stopped"))
            thread.join()
            scrapper.restore()
        
        if len(scrapper.server_list) == 0:
            console.print(
                Msg.get(f"commands.{self.name}.messages.noServersFound")
            )
            if self.logs_manager:
                self.logs_manager.write("\nNo servers found in websites")
        else:
            console.print(
                Msg.get(f"commands.websearch.messages.serversFound").replace(
                    "%servers%", str(len(scrapper.server_list))
                )
            )
            if self.logs_manager:
                self.logs_manager.write(
                    f"\nFound {len(scrapper.server_list)} servers in websites"
                )
        
        servers_data = GetServersData(scrapper.server_list, logs_manager=self.logs_manager)
        servers_data.ask_filters()
        servers_data.get_servers()
        return True