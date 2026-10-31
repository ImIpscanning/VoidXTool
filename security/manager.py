import os
import sys
import hashlib
from typing import Optional, Set
import requests
from ezjsonpy import get_config_value
from requests import RequestException, HTTPError, Timeout
from loguru import logger
from voidxtool.constants import UrlConstants
from voidxtool.utilities.obfuscator.obfuscator import Obfuscator

class NoOverrideMeta(type):
    """Metaclass to prevent overriding of protected attributes."""
    def __setattr__(cls, name, value):
        if name in ('_check', '_get_file_hash', '_get_hash_api', '_detect_unwanted_dlls', '_allowed_dlls', '_seen_dlls'):
            logger.debug(f"Attempt to override protected attribute: {name}")
            sys.exit(1)
        super().__setattr__(name, value)

class SecurityManager(metaclass=NoOverrideMeta):
    """Manages security checks for the application, including DLL validation and hash verification."""
    _allowed_dlls: Set[str] = {
        'libcrypto-3.dll', 'python3.dll', 'python313.dll', 'pythoncom313.dll', 'libssl-3.dll',
        'pywintypes313.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'libffi-8.dll', 'urlmon.dll',
        'iertutil.dll', 'pdh.dll', 'version.dll', 'srvcli.dll', 'fwpuclnt.dll', 'rasadhlp.dll',
        'propsys.dll', 'apphelp.dll', 'secur32.dll', 'wtsapi32.dll', 'uxtheme.dll',
        'windows.storage.dll', 'netutils.dll', 'iphlpapi.dll', 'dnsapi.dll', 'kernel.appcore.dll',
        'sspicli.dll', 'mswsock.dll', 'umpdc.dll', 'powrprof.dll', 'bcrypt.dll', 'win32u.dll',
        'crypt32.dll', 'bcryptprimitives.dll', 'kernelbase.dll', 'gdi32full.dll', 'wintypes.dll',
        'ucrtbase.dll', 'msvcp_win.dll', 'shell32.dll', 'shcore.dll', 'rpcrt4.dll', 'oleaut32.dll',
        'combase.dll', 'shlwapi.dll', 'kernel32.dll', 'ole32.dll', 'user32.dll', 'ws2_32.dll',
        'psapi.dll', 'gdi32.dll', 'imm32.dll', 'sechost.dll', 'nsi.dll', 'advapi32.dll',
        'msvcrt.dll', 'ntdll.dll', 'mdnsnsp.dll', 'wldp.dll'
    }
    _seen_dlls: Set[str] = set()

    def __init__(self):
        """Initialize the SecurityManager and perform initial security checks."""
        self._check()
        self._detect_unwanted_dlls()

    def _detect_unwanted_dlls(self) -> None:
        """
        Check for unauthorized or repeated DLLs loaded.
        If any suspicious or duplicated DLL names are detected, terminate the program.
        """
        if os.name != 'nt':
            return
        import psutil
        process = psutil.Process(os.getpid())
        dll_paths = [m.path.lower() for m in process.memory_maps() if m.path.lower().endswith('.dll')]
        seen_names = set()
        seen_paths = set()
        for dll_path in dll_paths:
            dll_name = os.path.basename(dll_path)
            if dll_name in seen_names:
                logger.error(f"DLL {dll_name} loaded more than once from different locations")
                sys.exit(1344)
            seen_names.add(dll_name)
            if dll_path in seen_paths:
                logger.error(f"DLL path {dll_path} loaded more than once")
                sys.exit(1345)
            seen_paths.add(dll_path)
            if dll_name not in self._allowed_dlls:
                logger.error(f"DLL {dll_name} is not allowed")
                sys.exit(1342)
        return

    def _check(self) -> None:
        """
        Performs a security check:
        - Ensures the script is being run from a frozen executable (e.g., via PyInstaller).
        - Computes the SHA-256 hash of the current executable.
        - Retrieves the expected (obfuscated) hash from an API and deobfuscates it.
        - Compares both hashes; if they don't match, the program exits.
        """
        if not (getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS')):
            logger.debug("Script was run from a frozen executable.")
            sys.exit(1)
        file_hash = self._get_file_hash()
        api_hash = self._get_hash_api()
        if api_hash is None:
            logger.debug("Script was run from a frozen executable. 2")
            sys.exit(1)
        deobfuscated_hash = Obfuscator().deobfuscate(obfuscated_text=api_hash)
        if deobfuscated_hash != file_hash:
            logger.debug("Invalid obfuscated hash detected.")
            sys.exit(1)

    @staticmethod
    def _get_file_hash() -> str:
        """
        Calculates the SHA-256 hash of the currently running executable file.
        :return: str - the hexadecimal digest of the hash
        """
        hasher = hashlib.sha256()
        with open(sys.executable, 'rb') as file:
            for chunk in iter(lambda: file.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _get_hash_api(self) -> Optional[str]:
        """
        Retrieves the expected hash from a remote API, depending on the OS.
        The response is expected to be a JSON object containing an obfuscated 'hash'.
        :return: Optional[str] - the obfuscated hash string, or None on failure
        """
        hash_url = UrlConstants.WINDOWS_HASH_URL if os.name == 'nt' else UrlConstants.LINUX_HASH_URL
        try:
            response = requests.get(hash_url)
            if response.status_code != 200:
                if get_config_value('debug'):
                    print(f"Requests failed in hash checker: Status code -> {response.status_code}")
                return None
            return response.json()['hash']
        except (KeyError, ValueError) as e:
            if get_config_value('debug'):
                print(f"Requests failed in hash checker: Invalid Json -> {e}")
            return None
        except (Timeout, ConnectionError, HTTPError, RequestException) as e:
            if get_config_value('debug'):
                print(f"Requests failed in hash checker: HTTP request error -> {e}")
            return None
        except Exception as e:
            if get_config_value('debug'):
                print(f"Requests failed in hash checker: Unexpected error -> {e}")
            return None