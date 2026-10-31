import time
from typing import Optional, Union
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.padding import Padding
from rich.box import SIMPLE_HEAVY
from rstatus.models import JavaServerResponse, BedrockServerResponse
from voidxtool.utilities.minecraft import ServerData, PlayerUUID
from voidxtool.utilities.input import Input
from voidxtool.commands.validator import Validator
from voidxtool.gui.language import Msg
from voidxtool.commands.base import BaseCommand
from voidxtool.logs import LogsManager

console = Console()

class ListeningCommand(BaseCommand):
    def __init__(self):
        super().__init__(name='listening')
        self.logs_manager = None
        self.ip_address = None
        self.port = None
        self.previous_players = []
        self.tracked_players = []
        self.target = None

    def custom_validate_arguments(self, user_arguments):
        '''
        Custom validation method to validate the ipinfo command arguments.
        :param user_arguments: list: The arguments to validate
        :return: bool: True if the arguments are valid, False otherwise
        '''
        self.target = user_arguments[0]
        if not (Validator.is_domain(domain=self.target) or 
                Validator.is_ip_and_port(ip=self.target) or 
                Validator.is_domain_and_port(domain=self.target)):
            console.print(Msg.get('errors.invalidServer'))
            return False
        return True

    def run(self, arguments, authentication):
        '''
        Run the server command.
        :param arguments: list: The arguments to run the command
        :param authentication: Authentication: Auth object
        :return: bool: True if the command was executed successfully, False otherwise
        '''
        if not self.validate_arguments(arguments):
            return False

        self.logs_manager = LogsManager(command_name=self.name)
        self.ip_address = None
        self.port = None
        self.previous_players = []
        self.tracked_players = []

        console.print(
            Msg.get(f'commands.{self.name}.messages.checkingServer')
               .replace('%server%', self.target)
        )

        server_data = ServerData(self.target, bot=False).get_data()
        if not server_data:
            console.print(Msg.get('errors.serverOffline'))
            return False

        if isinstance(server_data, BedrockServerResponse):
            console.print(Msg.get('errors.notJavaServer'))
            return False

        self.ip_address = server_data.ip_address
        self.port = server_data.port

        mode = Input(
            Msg.get(f'commands.{self.name}.messages.showPlayersMode'),
            input_type='string'
        ).get_input()

        if mode not in ('simple', 'table'):
            console.print(
                Msg.get(f'commands.{self.name}.messages.invalidShowPlayersMode')
            )
            return False

        self.logs_manager.write(f'Listening for players on server {server_data.ip_address}:{server_data.port}. Waiting players...\n')

        if mode == 'table':
            self._run_table_mode()
        else:
            self._run_simple_mode()

        return True

    def _build_table(self, players):
        '''
        Build a table with the provided player data
        :param players: List of player data
        :return: A padded table
        '''
        self.logs_manager.write('Building table..')
        table = Table(box=SIMPLE_HEAVY)
        table.add_column('Username', justify='center', style='bright_yellow', no_wrap=True)
        table.add_column('UUID', justify='center', style='bright_white', no_wrap=True)
        table.add_column('Online', justify='center', style='bright_white', no_wrap=True)
        table.add_column('Last Login', justify='center', style='bright_cyan', no_wrap=True)

        for player in players:
            if player['name'] == 'Anonymous Player' and player['id'] == '00000000-0000-0000-0000-000000000000':
                continue

            uuid_obj = PlayerUUID(username=player['name']).get_uuid_color(original_uuid=player['id'])
            player['uuidColor'] = uuid_obj
            uuid_color = ''

            if player['uuidColorMode'] == 'online':
                uuid_color = f'[green1]{player["id"]}[/green1]'
            elif player['uuidColorMode'] == 'offline':
                uuid_color = f'[red1]{player["id"]}[/red1]'
            elif player['uuidColorMode'] == 'unknown':
                uuid_color = f'[bright_magenta]{player["id"]}[/bright_magenta]'

            player['uuidColor'] = uuid_color
            player['online'] = True

            table.add_row(
                player['name'],
                uuid_color,
                '[green1]🟢[/green1]' if player['online'] else '[red1]🔴[/red1]',
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            )

        return Padding(table, (1, 1))

    def _run_table_mode(self):
        '''
        Run the listening command in table mode
        '''
        with Live(self._build_table(self.tracked_players), console=console, refresh_per_second=1) as live:
            while True:
                server_data = ServerData(self.target, bot=False).get_data()
                if not server_data:
                    console.print(Msg.get('errors.serverOffline'))
                    return

                current_players = server_data.players.sample or []
                new_players = [p for p in current_players if p not in self.tracked_players]
                disconnected_players = [p for p in self.tracked_players if p not in current_players]

                for player in disconnected_players:
                    if player['name'] in [p['name'] for p in self.previous_players]:
                        continue
                    player['online'] = False
                    self.logs_manager.write(
                        f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Player {player['name']} ({player['id']}) disconnected"
                    )
                    console.print(
                        Msg.get(f'commands.{self.name}.messages.disconnected')
                           .replace('%player%', player['name'])
                           .replace('%uuid%', player['uuidColor'])
                           .replace('%time%', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
                    )

                for player in new_players:
                    if player['name'] == 'Anonymous Player' and player['id'] == '00000000-0000-0000-0000-000000000000':
                        continue
                    if next((p for p in self.tracked_players if p['name'] == player['name']), None):
                        player['online'] = True
                        login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        console.print(
                            Msg.get(f'commands.{self.name}.messages.reconnected')
                               .replace('%player%', player['name'])
                               .replace('%uuid%', player['uuidColor'])
                               .replace('%time%', login_time)
                        )
                        self.logs_manager.write(
                            f"{login_time} - Player {player['name']} ({player['id']}) reconnected"
                        )
                    else:
                        player['online'] = True
                        self.tracked_players.append(player)
                        login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        console.print(
                            Msg.get(f'commands.{self.name}.messages.connected')
                               .replace('%player%', player['name'])
                               .replace('%uuid%', player['uuidColor'])
                               .replace('%time%', login_time)
                        )
                        self.logs_manager.write(
                            f"{login_time} - Player {player['name']} ({player['id']}) connected"
                        )

                self.previous_players = current_players
                live.update(self._build_table(self.tracked_players))
                time.sleep(1)

    def _run_simple_mode(self):
        '''
        Run the listening command in simple mode
        '''
        while True:
            server_data = ServerData(self.target, bot=False).get_data()
            if not server_data:
                console.print(Msg.get('errors.serverOffline'))
                return

            current_players = server_data.players.sample or []
            new_players = [p for p in current_players if p not in self.tracked_players]
            disconnected_players = [p for p in self.tracked_players if p not in current_players]

            for player in disconnected_players:
                if player['name'] in [p['name'] for p in self.previous_players]:
                    continue
                player['online'] = False
                self.logs_manager.write(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Player {player['name']} ({player['id']}) disconnected"
                )
                console.print(
                    Msg.get(f'commands.{self.name}.messages.disconnected')
                       .replace('%player%', player['name'])
                       .replace('%uuid%', player['uuidColor'])
                       .replace('%time%', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
                )

            for player in new_players:
                if player['name'] == 'Anonymous Player' and player['id'] == '00000000-0000-0000-0000-000000000000':
                    continue
                if next((p for p in self.tracked_players if p['name'] == player['name']), None):
                    player['online'] = True
                    login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    console.print(
                        Msg.get(f'commands.{self.name}.messages.reconnected')
                           .replace('%player%', player['name'])
                           .replace('%uuid%', player['uuidColor'])
                           .replace('%time%', login_time)
                    )
                    self.logs_manager.write(
                        f"{login_time} - Player {player['name']} ({player['id']}) reconnected"
                    )
                else:
                    player['online'] = True
                    self.tracked_players.append(player)
                    login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    console.print(
                        Msg.get(f'commands.{self.name}.messages.connected')
                           .replace('%player%', player['name'])
                           .replace('%uuid%', player['uuidColor'])
                           .replace('%time%', login_time)
                    )
                    self.logs_manager.write(
                        f"{login_time} - Player {player['name']} ({player['id']}) connected"
                    )

            self.previous_players = current_players
            time.sleep(1)