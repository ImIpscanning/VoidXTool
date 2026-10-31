import ast
import json
import requests
from loguru import logger
from voidxtool.auth import Authentication
from voidxtool.constants import UrlConstants
from voidxtool.utilities import URLFixer
from voidxtool.utilities.obfuscator.obfuscator import Obfuscator

class PasswordSearch:
    @staticmethod
    def search(authentication: Authentication, username: str):
        try:
            url = URLFixer.fix_double_slash(UrlConstants.DB_SEARCH_URL)
            params = {
                'system_code': authentication.system_code,
                'password': authentication.password,
                'username': authentication.username,
                'username_to_search': username.lower()
            }
            response = requests.get(url, params=params)
            data = json.loads(response.content)
            obfuscated = data.get('data', '')
            deobfuscated = Obfuscator().deobfuscate(obfuscated)
            result = ast.literal_eval(deobfuscated) if deobfuscated else []
            return result
        except Exception as e:
            logger.warning(f"Error in password command! {e}")
            return []

    @staticmethod
    def searchs(authentication: Authentication, usernames: list[str]):
        results = []
        for username in usernames:
            res = PasswordSearch.search(authentication, username)
            results.append(res)
        return results
