import base64
from typing import Optional
from loguru import logger

class Obfuscator:
    def __init__(self):
        self.key = 'YYw++_{iRx1OtY.,v=Xx$85xUh#^pTkT3h%8/4j.j}MNwX0-v2'

    def obfuscate(self, text: str) -> str:
        '''
        Obfuscate the given text using XOR with the key and encode it to base64.
        :param text: Text to obfuscate
        :return: Obfuscated text
        '''
        try:
            key = self.key
            xored = ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(text, key * (len(text) // len(key) + 1)))
            return base64.urlsafe_b64encode(xored.encode()).decode()
        except Exception as e:
            logger.warning(f"Error obfuscating text: {e}")
            return text

    def deobfuscate(self, obfuscated_text: str) -> Optional[str]:
        '''
        Deobfuscate the given obfuscated text using XOR with the key and decode it from voidxtool.commands.base64.
        :param obfuscated_text: Obfuscated text to deobfuscate
        :return: Deobfuscated text
        '''
        try:
            key = self.key
            decoded = base64.urlsafe_b64decode(obfuscated_text.encode()).decode()
            xored = ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(decoded, key * (len(decoded) // len(key) + 1)))
            return xored
        except Exception as e:
            logger.warning(f"Error deobfuscating text: {e}")
            return None