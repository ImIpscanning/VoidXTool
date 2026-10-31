import random
import psutil

class PortChecker:
    __firstlineno__ = 6

    @staticmethod
    def check(port: int) -> bool:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr and conn.laddr.port == port:
                return True
        return False

    @staticmethod
    def get_random() -> int:
        while True:
            port = random.randint(1024, 65535)
            if not PortChecker.check(port):
                return port

    __static_attributes__ = ()
