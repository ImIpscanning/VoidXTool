import os
import sys
import shutil
import requests
import subprocess
import time
import ctypes
if os.name == 'nt':
    import winshell
    import winreg
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TaskID
from voidxtool.constants import VoidXToolConstants, UrlConstants
from voidxtool.files import VoidXToolPath

console: Console = Console()
uninstall_script: str = r'''
@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Check if VoidXTool.exe is running
tasklist /FI "IMAGENAME eq VoidXTool.exe" | find /I "VoidXTool.exe" >nul
IF ERRORLEVEL 1 (
    echo VoidXTool is not running.
) ELSE (
    echo Please close VoidXTool before uninstalling. Exiting in 3 seconds...
    timeout /t 3 /nobreak >nul
    exit
)

:: Set paths for files and folders
SET APPDATA_PATH=%APPDATA%\VoidXTool
SET VOIDXTOOLDATA_PATH=%APPDATA%\VoidXToolData
SET REGISTRY_PATH=Software\Microsoft\Windows\CurrentVersion\Uninstall\VoidXTool
SET SHORTCUT_PATH="%APPDATA%\Microsoft\Windows\Start Menu\Programs\VoidXTool.lnk"

:: Function to remove VoidXTool folder
:REMOVE_FOLDERS
echo Removing VoidXTool folder...
IF EXIST !APPDATA_PATH! (
    rmdir /s /q !APPDATA_PATH!
    echo VoidXTool folder removed successfully.
) ELSE (
    echo VoidXTool folder not found.
)

:: Function to remove VoidXToolData folder
echo Removing VoidXToolData folder...
IF EXIST !VOIDXTOOLDATA_PATH! (
    rmdir /s /q !VOIDXTOOLDATA_PATH!
    echo VoidXToolData folder removed successfully.
) ELSE (
    echo VoidXToolData folder not found.
)

:: Function to remove the shortcut
:REMOVE_SHORTCUT
echo Removing shortcut...
IF EXIST !SHORTCUT_PATH! (
    del !SHORTCUT_PATH!
    echo Shortcut removed successfully.
) ELSE (
    echo Shortcut not found.
)

:: Function to remove the desktop shortcut
:REMOVE_DESKTOP_SHORTCUT
echo Removing desktop shortcut...
IF EXIST "%USERPROFILE%\Desktop\VoidXTool.lnk" (
    del "%USERPROFILE%\Desktop\VoidXTool.lnk"
    echo Desktop shortcut removed successfully.
) ELSE (
    echo Desktop shortcut not found.
)

:: Function to remove the registry key
:REMOVE_REGISTRY_KEY
echo Removing registry key...
reg delete HKCU\!REGISTRY_PATH! /f >nul 2>&1
IF ERRORLEVEL 1 (
    echo Registry key not found.
) ELSE (
    echo Registry key removed successfully.
)

echo Uninstallation complete.

:: Create a temporary script to delete this script
echo @echo off > "%TEMP%\delete_uninstall.bat"
echo timeout /t 1 > NUL >> "%TEMP%\delete_uninstall.bat"
echo del "%~f0" >> "%TEMP%\delete_uninstall.bat"
echo exit >> "%TEMP%\delete_uninstall.bat"
start "" "%TEMP%\delete_uninstall.bat"

timeout /t 1 /nobreak >nul
EXIT
'''
class WindowsInstaller:
    def __init__(self):
        self.record_path = 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\VoidXTool'
        self.appdata_path = os.path.join(os.getenv('APPDATA'), 'VoidXTool')
        self.uninstall_path = os.path.join(os.getenv('APPDATA'), 'uninstall.bat')
        self.start_menu_path = os.path.join(winshell.start_menu(), 'Programs', 'VoidXTool.lnk')
        self.temp_path = os.getenv('TEMP')

    def install(self):
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Installing VoidXTool...")
        self._download_voidxtool()
        self._copy_file()
        self._create_registry_key()
        self._create_shortcut()
        self._create_desktop_shortcut()
        self._create_uninstall_script()
        console.print(f"{VoidXToolConstants.INFO_PREFIX} VoidXTool installed successfully.")
        time.sleep(1)
        self._execute_commands_after_install()
        sys.exit(0)

    def update(self):
        data_path = VoidXToolPath.get_voidxtool_data_path()
        portable_path = os.path.join(data_path, 'portable.voidxtool')
        if os.path.exists(portable_path):
            console.print(f"{VoidXToolConstants.WARNING_PREFIX} VoidXTool is in portable mode. Please update manually.")
            time.sleep(3)
            sys.exit(1)
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Updating VoidXTool...")
        self._download_voidxtool()
        self._execute_commands_after_update()
        console.print(f"{VoidXToolConstants.INFO_PREFIX} VoidXTool updated successfully. Finishing...")
        sys.exit(0)

    def _download_voidxtool(self):
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Downloading the latest version of VoidXTool...")
        if os.name == 'nt':
            filename = 'New-VoidXTool.exe'
            url = UrlConstants.WINDOWS_BINARY_URL
        else:
            filename = 'New-VoidXTool'
            url = UrlConstants.LINUX_BINARY_URL
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_length = int(response.headers.get('Content-Length', 0))
            chunk_size = 1024
            with Progress("[progress.description]{task.description}", BarColumn(), "[progress.percentage]{task.percentage:>3.1f}%", "•", TimeRemainingColumn()) as progress:
                task = progress.add_task(f"[bright_black][[bright_green]#[/bright_green]][/bright_black] [bright_white]Downloading {filename}...[/bright_white]", total=total_length)
                file_path = os.path.join(self.appdata_path, filename)
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            progress.advance(task, len(chunk))
        except requests.exceptions.RequestException as e:
            console.print(f"{VoidXToolConstants.WARNING_PREFIX} Error downloading the latest version of VoidXTool: {e}")
            time.sleep(3)
            sys.exit(1)

    def _copy_file(self):
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Copying file to the AppData folder...")
        if os.path.exists(self.appdata_path):
            console.print(f"{VoidXToolConstants.WARNING_PREFIX} Folder already exists. Removing...")
            shutil.rmtree(self.appdata_path)
        os.makedirs(self.appdata_path, exist_ok=True)
        src = sys.executable
        dst = os.path.join(self.appdata_path, 'VoidXTool.exe')
        try:
            console.print(f"{VoidXToolConstants.INFO_PREFIX} Copying file...")
            shutil.copy(src, dst)
            console.print(f"{VoidXToolConstants.INFO_PREFIX} File copied successfully.")
        except Exception as e:
            console.print(f"{VoidXToolConstants.WARNING_PREFIX} Error copying file: {e}")
            Prompt.ask(f"{VoidXToolConstants.PREFIX} [bright_white]Press Enter to exit...")
            sys.exit(1)

    def _create_registry_key(self):
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Creating registry key...")
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.record_path)
        winreg.SetValueEx(key, 'DisplayName', 0, winreg.REG_SZ, 'VoidXTool')
        winreg.SetValueEx(key, 'DisplayVersion', 0, winreg.REG_SZ, VoidXToolConstants.VERSION)
        winreg.SetValueEx(key, 'Publisher', 0, winreg.REG_SZ, 'wRRulos')
        winreg.SetValueEx(key, 'UninstallString', 0, winreg.REG_SZ, self.uninstall_path)
        winreg.SetValueEx(key, 'ModifyPath', 0, winreg.REG_SZ, self.uninstall_path)
        winreg.SetValueEx(key, 'NoModify', 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(key, 'NoRepair', 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, 'DisplayIcon', 0, winreg.REG_SZ, os.path.join(VoidXToolPath.get_voidxtool_data_path(), 'icon.ico'))
        winreg.CloseKey(key)
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Registry key created successfully.")

    def _create_shortcut(self):
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Creating shortcut in the Start Menu...")
        with winshell.shortcut(self.start_menu_path) as shortcut:
            shortcut.path = os.path.join(self.appdata_path, 'VoidXTool.exe')
            shortcut.arguments = ""
            shortcut.description = "VoidXTool - Minecraft Pentesting Tool"
            shortcut.icon_location = (os.path.join(VoidXToolPath.get_voidxtool_data_path(), 'icon.ico'), 0)
            shortcut.working_directory = self.appdata_path
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Shortcut created successfully.")

    def _create_desktop_shortcut(self):
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Creating shortcut on the desktop...")
        desktop_path = os.path.join(winshell.desktop(), 'VoidXTool.lnk')
        with winshell.shortcut(desktop_path) as shortcut:
            shortcut.path = os.path.join(self.appdata_path, 'VoidXTool.exe')
            shortcut.arguments = ""
            shortcut.description = "VoidXTool - Minecraft Pentesting Tool"
            shortcut.icon_location = (os.path.join(VoidXToolPath.get_voidxtool_data_path(), 'icon.ico'), 0)
            shortcut.working_directory = self.appdata_path
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Desktop shortcut created successfully.")

    def _create_uninstall_script(self):
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Creating uninstall script...")
        with open(self.uninstall_path, 'w') as f:
            f.write(uninstall_script)
        console.print(f"{VoidXToolConstants.INFO_PREFIX} Uninstall script created successfully.")

    def _execute_commands_after_update(self):
        subprocess.Popen([os.path.join(self.appdata_path, 'VoidXTool.exe')])

    def _execute_commands_after_install(self):
        subprocess.Popen([os.path.join(self.appdata_path, 'VoidXTool.exe')])
