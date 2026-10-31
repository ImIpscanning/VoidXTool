import hashlib
import uuid
from json import JSONDecodeError
from typing import Optional
import requests

class PlayerUUIDFormat:
    def __init__(self, online_uuid: Optional[str], offline_uuid: Optional[str]):
        self.online_uuid = online_uuid
        self.offline_uuid = offline_uuid

class PlayerUUID:
    def __init__(self, username: str):
        self.username = username

    def get_uuid(self) -> PlayerUUIDFormat:
        online_uuid = None
        try:
            response = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{self.username}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                online_uuid = data.get('id')
                if online_uuid:
                    online_uuid = str(uuid.UUID(online_uuid))
        except (requests.RequestException, JSONDecodeError, KeyError):
            online_uuid = None
        offline_uuid = self._get_offline_uuid()
        return PlayerUUIDFormat(online_uuid, offline_uuid)

    def get_uuid_color(self, original_uuid: str) -> str:
        if not original_uuid:
            return "unknown"
        original_uuid = original_uuid.replace('-', '')
        first_char = original_uuid[0].lower()
        if first_char in '01234567':
            return "red"
        elif first_char in '89abcdef':
            return "blue"
        return "unknown"

    def _get_offline_uuid(self) -> str:
        name = f"OfflinePlayer:{self.username}"
        md5 = hashlib.md5(name.encode('utf-8')).digest()
        offline_uuid = uuid.UUID(bytes=md5[:16], version=3)
        return str(offline_uuid)