import re
from typing import Optional

class TimeConverter:
    @staticmethod
    def convert_time(message: str) -> Optional[int]:
        pattern = r'^(\d+)(s|m|h|d)$'
        match = re.match(pattern, message)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            if unit == 's':
                return value
            elif unit == 'm':
                return value * 60
            elif unit == 'h':
                return value * 3600
            elif unit == 'd':
                return value * 86400
        return None