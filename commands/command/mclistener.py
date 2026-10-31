from voidxtool.commands.base import BaseCommand
from voidxtool.auth import Authentication
from voidxtool.logs import LogsManager
from voidxtool.utilities.tcp.listener import TCPListener

class MCListenerCommand(BaseCommand):
    def __init__(self):
        super().__init__(name='mclistener')

    def run(self, arguments, authentication):
        '''
        Run the server command.

        :param arguments: list: The arguments to run the command
        :param authentication: Authentication: Auth object
        :return: bool: True if the command was executed successfully, False otherwise
        '''
        logs_manager = LogsManager(command_name=self.name)
        servers = TCPListener().get_minecraft_servers()
        logs_manager.write(f"Retrieved {len(servers)} Minecraft servers")
        return True