import os
from dataclasses import dataclass
from voidxtool.files.path import VoidXToolPath

_OPTIONAL_API_BASE = os.getenv("VOIDXTOOL_API_BASE_URL", "").rstrip("/")

@dataclass
class VoidXToolConstants:
    """Constants for VoidXTool"""
    VERSION: str = "3.2.0"
    PREFIX: str = "[bright_black][[red1]#[bright_black]]"
    INFO_PREFIX: str = "[bright_black][[green1]INFO[bright_black]][bright_white]"
    WARNING_PREFIX: str = "[bright_black][[yellow1]WARNING[bright_black]][bright_white]"
    INPUT_PREFIX: str = "[bright_black][[cyan1]#[bright_black]][bright_white]"
    LANGUAGES: tuple = ("en", "es", "ru", "ur", "fr", "fa", "de", "pt", "ja")
    LANGUAGES_JSON: tuple = ("en.json", "es.json", "ru.json", "ur.json", "fr.json", "fa.json", "de.json", "pt.json", "ja.json")
    SPACES: str = "  "
    DISCORD_CLIENT_ID: int = 0x11BC5A4E3D00007A

@dataclass
class UrlConstants:
    """Optional external endpoints.

    No public VoidXTool backend is assumed. Set VOIDXTOOL_API_BASE_URL only
    when an owner-controlled service has been deployed and reviewed.
    """
    API_BASE_URL: str = _OPTIONAL_API_BASE
    API_FINDER_ENDPOINT: str = f"{API_BASE_URL}/finder" if API_BASE_URL else ""
    LOGIN_URL: str = f"{API_BASE_URL}/auth/login" if API_BASE_URL else ""
    VOIDXTOOL_FILES_URL: str = f"{API_BASE_URL}/resources/" if API_BASE_URL else ""
    WINDOWS_BINARY_URL: str = f"{API_BASE_URL}/resources/windows" if API_BASE_URL else ""
    LINUX_BINARY_URL: str = f"{API_BASE_URL}/resources/linux" if API_BASE_URL else ""
    VOIDXTOOL_VERSION_URL: str = f"{API_BASE_URL}/version" if API_BASE_URL else ""
    DB_SEARCH_URL: str = f"{API_BASE_URL}/dbs/search" if API_BASE_URL else ""
    DB_MULTIPLE_SEARCH_URL: str = f"{API_BASE_URL}/dbs/searchs" if API_BASE_URL else ""
    WINDOWS_HASH_URL: str = f"{API_BASE_URL}/hash/windows" if API_BASE_URL else ""
    LINUX_HASH_URL: str = f"{API_BASE_URL}/hash/linux" if API_BASE_URL else ""
    DISCORD_INVITE_URL: str = os.getenv("VOIDXTOOL_DISCORD_URL", "")
    VOIDXTOOL_WEBSITE_URL: str = os.getenv("VOIDXTOOL_WEBSITE_URL", "")

@dataclass
class NodeJSConstants:
    """Constants for Node.js"""
    NODEJS_COMMAND: str = "node"
    BOT_FILE_NAME: str = "./voidxtoolBot.js" if os.name == "posix" else "voidxtoolBot.js"
    BOTTER_FILE_NAME: str = "./botter.mjs" if os.name == "posix" else "botter.mjs"
    CONNECT_FILE_NAME: str = "./connect.mjs" if os.name == "posix" else "connect.mjs"
    KICK_FILE_NAME: str = "./kick.mjs" if os.name == "posix" else "kick.mjs"
    _BOT_COMMAND: str = f"cd {VoidXToolPath.get_voidxtool_data_path()} && {NODEJS_COMMAND} --no-deprecation"
    BOT_COMMAND: str = f"C: && {_BOT_COMMAND}" if os.name == "nt" else _BOT_COMMAND

@dataclass
class WebConstants:
    """Constants for web"""
    USER_AGENTS: tuple = (
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0"},
        {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15"},
        {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0"},
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A5341f Safari/604.1"},
        {"User-Agent": "Mozilla/5.0 (iPad; CPU OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Mobile/15E148 Safari/604.1"},
        {"User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Linux; Android 9; SAMSUNG SM-A520F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.136 Mobile Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.91 Mobile Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Linux; Android 7.1.1; Nexus 6P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36"},
    )
