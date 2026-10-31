import time
import random
from typing import Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rstatus.models import JavaServerResponse, BedrockServerResponse
from mccolors import mcwrite
from voidxtool.auth import Authentication
from voidxtool.logs import LogsManager
from voidxtool.utilities.minecraft import ServerData
from voidxtool.commands.base import BaseCommand
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg
from voidxtool.utilities.minecraft import MineflayerKick, BotResponse
from voidxtool.utilities.input import Input
from voidxtool.utilities.checker import SocksChecker
from voidxtool.utilities.scrapper import FreeProxies
from voidxtool.utilities.app_checker import AppChecker
from voidxtool.constants import VoidXToolConstants

console = Console()

class KickAllCommand(BaseCommand):
    def __init__(self):
        super().__init__(name='kickall')
        self.logs_manager = None
        self.stopped = False
        self.executor = None
        self.target = None
        self.version = None

    def custom_validate_arguments(self, user_arguments):
        '''
        Custom validation method to validate the server command arguments.
        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        '''
        self.target = user_arguments[0]
        self.version = user_arguments[1]
        if not (Validator.is_domain(domain=self.target) or 
                Validator.is_ip_and_port(ip=self.target) or 
                Validator.is_domain_and_port(domain=self.target)):
            console.print(Msg.get('errors.invalidServer'))
            return False
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

        if not AppChecker().nodejs_installed:
            console.print(f"{VoidXToolConstants.PREFIX} [bright_white]NodeJS is not installed. Please install it and restart VoidXTool.")
            return False

        self.logs_manager = LogsManager(command_name=self.name)
        console.print(Msg.get(f'commands.{self.name}.messages.checkingServer').replace('%server%', self.target))

        server_data = ServerData(self.target, authentication=authentication).get_data()
        if not server_data:
            console.print(Msg.get('errors.serverOffline'))
            return False
        if not isinstance(server_data, JavaServerResponse):
            console.print(Msg.get('errors.notJavaServer'))
            return False

        ip_address, port = self.target.split(':') if ':' in self.target else (self.target, '25565')
        port = int(port)
        players = server_data.players
        if not players:
            console.print(Msg.get(f'commands.{self.name}.messages.noPlayers'))
            return False

        use_proxies = Input.get_input(input_message=Msg.get(f'commands.{self.name}.messages.proxyAsk'), input_type='boolean')
        proxies = []
        if use_proxies:
            use_custom_proxies = Input.get_input(input_message=Msg.get(f'commands.{self.name}.messages.customProxiesAsk'), input_type='boolean')
            if not use_custom_proxies:
                console.print(Msg.get(f'commands.{self.name}.messages.gettingFreeProxies'))
                proxies = FreeProxies.get_all_valid_proxies()
                if not proxies:
                    console.print(Msg.get(f'commands.{self.name}.messages.failedToGetFreeProxies'))
                    return False
            else:
                proxy_file = Input.get_input(input_message=Msg.get(f'commands.{self.name}.messages.customProxies'), input_type='file')
                try:
                    with open(proxy_file, 'r') as f:
                        proxies = [line.strip() for line in f.readlines() if line.strip()]
                    proxies = SocksChecker(proxies=proxies).proxies
                    if not proxies:
                        console.print(Msg.get(f'commands.{self.name}.messages.invalidCustomProxies').replace('%file%', proxy_file))
                        return False
                except Exception:
                    console.print(Msg.get(f'commands.{self.name}.messages.invalidCustomProxies').replace('%file%', proxy_file))
                    return False

        exclude_players = Input.get_input(input_message=Msg.get(f'commands.{self.name}.messages.excludingPlayerAsk'), input_type='string')
        excluded = [exclude_players] if exclude_players else []
        console.print(Msg.get(f'commands.{self.name}.messages.excludingPlayer').replace('%username%', exclude_players) if exclude_players else '')

        loop_execution = Input.get_input(input_message=Msg.get(f'commands.{self.name}.messages.loopExecutionAsk'), input_type='boolean')

        def kick_player(player, proxy=None):
            if self.stopped:
                return None
            if player['name'] in excluded:
                console.print(Msg.get('commands.kickall.messages.excludingUser').replace('%username%', player['name']))
                return None
            username = player['name']
            console.print(Msg.get('commands.kick.messages.kicking')
                         .replace('%server%', f'{ip_address}:{port}')
                         .replace('%username%', username)
                         .replace('%version%', self.version))
            self.logs_manager.write(f'Calling MineflayerKick...')
            bot = MineflayerKick(ip_address=ip_address, port=port, version=self.version, username=username, proxy=proxy)
            response = bot.get_response()
            self.logs_manager.write(f'Response: {response} (0)')
            if response == '[BOT] Connected':
                console.print(Msg.get('commands.kick.messages.playerKicked').replace('%username%', username))
            else:
                response = BotResponse.get_bot_color_response(response=response)
                console.print(Msg.get('commands.kick.messages.errorKickingPlayer')
                             .replace('%username%', username)
                             .replace('%reason%', ''))
                mcwrite(response)
            return username

        try:
            while True:
                console.print(Msg.get(f'commands.{self.name}.messages.gettingPlayers'))
                server_data = ServerData(self.target, authentication=authentication).get_data()
                if not server_data:
                    console.print(Msg.get(f'commands.{self.name}.messages.serverOffline').replace('%seconds%', '4'))
                    time.sleep(4)
                    continue
                if not isinstance(server_data, JavaServerResponse):
                    console.print(Msg.get(f'commands.{self.name}.messages.notJavaServer'))
                    time.sleep(4)
                    continue
                players = server_data.players
                if not players:
                    console.print(Msg.get(f'commands.{self.name}.messages.noPlayersFoundLoop'))
                    time.sleep(4)
                    continue

                self.executor = ThreadPoolExecutor(max_workers=len(proxies) or 10)
                futures = []
                for player in players:
                    if self.stopped:
                        break
                    if player['name'] in excluded:
                        continue
                    proxy = random.choice(proxies) if proxies else None
                    futures.append(self.executor.submit(kick_player, player, proxy))
                
                for future in as_completed(futures):
                    if self.stopped:
                        break
                    result = future.result()
                    if result and result == players[-1]['name']:
                        time.sleep(1)
                
                if not loop_execution:
                    console.print(Msg.get(f'commands.{self.name}.messages.playersKicked'))
                    break
                console.print(Msg.get(f'commands.{self.name}.messages.playersKickedLoop').replace('%seconds%', str(4)))
                time.sleep(4)

        except KeyboardInterrupt:
            self.stopped = True
            console.print(Msg.get(f'commands.{self.name}.messages.stopped'))
            if self.executor:
                self.executor.shutdown(wait=False)
        except Exception:
            console.print(Msg.get(f'commands.{self.name}.messages.stoppingLoop'))

        if self.executor:
            self.executor.shutdown(wait=False)
        return True