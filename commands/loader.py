from voidxtool.commands.command import (
    HelpCommand, AuditCommand, ShodanCommand, AltsCommand, AnyDeskGBCommand, DdosCommand, DeashCommand, ScrapperCommand,
    ProtectionCommand, ReverseProxyCommand, PHP2ShellCommand,
    ServerCommand, UuidCommand, IPInfoCommand, IPHistoryCommand, DnsRecordsCommand,
    CheckerCommand, SubdomainsCommand, WebSearchCommand, ScanCommand, AutoScanCommand,
    ListeningCommand, ProxyCommand, FakeProxyCommand, ConnectCommand, SendCMDCommand,
    KickCommand, KickAllCommand, BotAttackCommand, RconCommand, BruteRconCommand,
    ShellCommand, MCListenerCommand, CustomPortCommand, WebhookCommand, ClearServersCommand,
    LanguageCommand, SettingsCommand, HistoryCommand, DebugCommand, ServerDataCommand,
    ClearCommand, RandomServers, PasswordCommand, VulnServerCommand, PterodactylCommand
)

class CommandLoader:
    __firstlineno__ = 9

    @staticmethod
    def load_commands():
        '''
        Load all available commands into a dictionary.
        :return: A dictionary containing all available commands.
        '''
        return {
            'help': HelpCommand(),
            'audit': AuditCommand(),
            'shodan': ShodanCommand(),
            'alts': AltsCommand(),
            'anydeskgb': AnyDeskGBCommand(),
            'ddos': DdosCommand(),
            'deash': DeashCommand(),
            'scrapper': ScrapperCommand(),
            'protection': ProtectionCommand(),
            'reverseproxy': ReverseProxyCommand(),
            'php2shell': PHP2ShellCommand(),
            'server': ServerCommand(),
            'uuid': UuidCommand(),
            'ipinfo': IPInfoCommand(),
            'iphistory': IPHistoryCommand(),
            'dnsrecords': DnsRecordsCommand(),
            'checker': CheckerCommand(),
            'subdomains': SubdomainsCommand(),
            'websearch': WebSearchCommand(),
            'scan': ScanCommand(),
            'autoscan': AutoScanCommand(),
            'listening': ListeningCommand(),
            'proxy': ProxyCommand(),
            'fakeproxy': FakeProxyCommand(),
            'connect': ConnectCommand(),
            'sendcmd': SendCMDCommand(),
            'kick': KickCommand(),
            'kickall': KickAllCommand(),
            'botattack': BotAttackCommand(),
            'rcon': RconCommand(),
            'brutercon': BruteRconCommand(),
            'shell': ShellCommand(),
            'password': PasswordCommand(),
            'mclistener': MCListenerCommand(),
            'customport': CustomPortCommand(),
            'webhook': WebhookCommand(),
            'vulnserver': VulnServerCommand(),
            'pterodactyl': PterodactylCommand(),
            'clearservers': ClearServersCommand(),
            'language': LanguageCommand(),
            'settings': SettingsCommand(),
            'history': HistoryCommand(),
            'debug': DebugCommand(),
            'serverdata': ServerDataCommand(),
            'randomservers': RandomServers(),
            'clear': ClearCommand()
        }

    __static_attributes__ = ()
