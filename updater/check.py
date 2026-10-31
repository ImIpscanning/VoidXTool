import requests
from loguru import logger
from voidxtool.constants import UrlConstants, VoidXToolConstants
from voidxtool.utilities.url import URLFixer

class UpdaterCheck:
    @staticmethod
    def update_available() -> bool:
        """
        Check if a new version is available
        :return: bool
        """
        if not UrlConstants.VOIDXTOOL_VERSION_URL:
            return False
        try:
            response = requests.get(
                URLFixer.fix_double_slash(UrlConstants.VOIDXTOOL_VERSION_URL),
                timeout=5,
            )
            if response.status_code != 200:
                return False
            version = response.json()['version']
            if version != VoidXToolConstants.VERSION:
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False
