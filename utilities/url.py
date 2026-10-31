import re
from typing import Literal
from urllib.parse import urlparse, urlunparse, ParseResult

class URLFixer:
    @staticmethod
    def fix_double_slash(url: str) -> str:
        '''
Method to fix double slashes in the URL
:param url: str: The URL to fix
:return: str: The fixed URL
'''
        parsed = urlparse(url)
        fixed_path = re.sub(r'/+', '/', parsed.path)
        fixed_url = urlunparse(parsed._replace(path=fixed_path))
        return str(fixed_url)

    @staticmethod
    def extract_host(url: str) -> str:
        '''
Extract the hostname from a URL.

:param str url: The URL to extract from.
:return str: The hostname.
'''
        parsed = urlparse(url)
        return parsed.hostname