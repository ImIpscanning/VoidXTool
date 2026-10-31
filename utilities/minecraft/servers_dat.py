import os
from typing import Union
from voidxtool.utilities.termux.utils import TermuxUtilities
from voidxtool.gui.language.get_message import Messages as Msg
from voidxtool.utilities.input.get_input import Input
from voidxtool.utilities.minecraft.get_servers import ServersFound

class ServersDAT:
    def __init__(self):
        self.servers_dat_file_path = self.get_servers_dat_file_path()

    def ask_save_servers(self, servers):
        '''
        Method to ask the user if they want to save 
        the servers to the servers.dat file.
        '''
        if TermuxUtilities.is_termux():
            return None
        answer = Input.get(Msg.get('addServers.addServersFoundToMinecraft'), 'boolean')
        if answer:
            only_bungee = Input.get(Msg.get('addServers.addBungeeExploitVulnerableServersOnly'), 'boolean')
            if only_bungee:
                vulnerable_servers = [s for s in servers if getattr(s, 'bungee_vulnerable', False)]
                self.add_servers_dat_file(vulnerable_servers, True)
            else:
                self.add_servers_dat_file(servers, False)

    def add_servers_dat_file(self, servers, vulnerable):
        '''
        Method to add a server to the servers.dat file.
        :param servers: The server to add to the servers.dat file
        :param vulnerable: True if the server is vulnerable, False otherwise
        '''
        if TermuxUtilities.is_termux():
            return None
        try:
            with open(self.servers_dat_file_path, 'a', encoding='utf-8') as f:
                for server in servers:
                    line = f"{server.ip_address}:{server.port}"
                    if vulnerable:
                        line += " #VULNERABLE"
                    f.write(line + "\n")
        except Exception as e:
            pass

    @staticmethod
    def get_servers_dat_file_path():
        if os.name == 'nt':
            return os.path.join(os.environ['APPDATA'], '.minecraft', 'servers.dat')
        else:
            return os.path.join(os.path.expanduser('~'), '.minecraft', 'servers.dat')

    def remove_servers_dat_file(self):
        '''Method to remove the servers.dat file.'''
        if os.path.exists(self.servers_dat_file_path):
            os.remove(self.servers_dat_file_path)