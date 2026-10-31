from json import JSONDecodeError
from typing import Optional
import requests
from loguru import logger

class PlayerUsername:
    def __init__(self, uuid: str):
        self.uuid = uuid

    @logger.catch
    def get_username(self) -> Optional[str]:
        try:
            response = requests.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{self.uuid}')
            if response.status_code != 200:
                return None
            data = response.json()
            return data.get('name')
        except (JSONDecodeError, KeyError, requests.exceptions.HTTPError) as ex:
            logger.error(f'Failed to get the username of the player with UUID: {self.uuid}')
            return None