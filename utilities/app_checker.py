import subprocess
import os
from ezjsonpy import get_config_value
from rich.console import Console
from voidxtool.files import VoidXToolPath
from voidxtool.gui.language import Msg

console: Console = Console()

class AppChecker:
    @staticmethod
    def nmap_installed() -> bool:
        """
        Check if Nmap is installed.
        :return: True if Nmap is installed, False otherwise.
        """
        nmap_command = get_config_value("nmapCommand")
        return subprocess.call(f"{nmap_command} --version >nul 2>&1", shell=True) == 0

    @staticmethod
    def masscan_installed() -> bool:
        """
        Check if Masscan is installed and return the output.
        :return: True if Masscan is installed, False otherwise, Output from Masscan command
        """
        scanners_path = os.path.join(VoidXToolPath.get_voidxtool_data_path(), "scanners")
        masscan_command = str(get_config_value("masscanCommand"))
        command = f"cd {scanners_path} && {masscan_command} --version"
        
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )
        
        output = result.stdout.strip() or result.stderr.strip()
        
        if "Permission denied" in output:
            masscan_file = "masscan"
            fix_command = f"chmod +x {scanners_path}/{masscan_file}"
            console.print(
                Msg.get("errors.permissionDenied")
                .replace("%file%", masscan_file)
                .replace("%commandToFix%", fix_command)
            )
            return False
            
        if "Masscan version" not in output:
            return False
            
        return True

    @staticmethod
    def nodejs_installed() -> bool:
        """
        Check if Node.js is installed.
        :return: True if Node.js is installed, False otherwise.
        """
        return subprocess.call("node --version >nul 2>&1", shell=True) == 0