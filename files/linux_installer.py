import os
import sys
import shutil
from typing import Optional
import requests
import subprocess
import time
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TaskID
from voidxtool.constants import VoidXToolConstants, UrlConstants
from voidxtool.files import VoidXToolPath

console: Console = Console()

class LinuxInstaller:
    def __init__(self):
        self.install_path = '/usr/local/bin/voidxtool'
        self.desktop_entry_path = '/usr/share/applications/voidxtool.desktop'

    def install(self):
        console.print("[bold green]Starting installation of VoidXTool...[/bold green]")
        self._download_voidxtool()
        self._copy_file()
        self._set_permissions()
        self._create_desktop_entry()
        self._execute_commands_after_install()
        console.print("[bold green]VoidXTool installed successfully![/bold green]")

    def update(self):
        console.print("[bold yellow]Updating VoidXTool...[/bold yellow]")
        self._download_voidxtool()
        self._copy_file()
        self._set_permissions()
        self._execute_commands_after_update()
        console.print("[bold green]VoidXTool updated successfully![/bold green]")

    def uninstall(self):
        console.print("[bold red]Uninstalling VoidXTool...[/bold red]")
        self._remove_folders()
        self._remove_desktop_entry()
        console.print("[bold green]VoidXTool uninstalled successfully![/bold green]")

    def _download_voidxtool(self):
        url = UrlConstants.MCPT_TOOL_LINUX_URL
        local_filename = "/tmp/voidxtool"
        with Progress("[progress.description]{task.description}", BarColumn(), TimeRemainingColumn()) as progress:
            task = progress.add_task("Downloading VoidXTool...", total=100)
            response = requests.get(url, stream=True)
            total_length = response.headers.get('content-length')
            if total_length is None:
                with open(local_filename, 'wb') as f:
                    f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                with open(local_filename, 'wb') as f:
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        progress.update(task, completed=int(dl * 100 / total_length))
        self.downloaded_file = local_filename

    def _copy_file(self):
        shutil.copy(self.downloaded_file, self.install_path)

    def _remove_folders(self):
        if os.path.exists(self.install_path):
            os.remove(self.install_path)
        data_folder = VoidXToolPath.DATA_FOLDER
        if os.path.exists(data_folder):
            shutil.rmtree(data_folder)

    def _create_desktop_entry(self):
        entry = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=VoidXTool\n"
            f"Exec={self.install_path}\n"
            "Icon=utilities-terminal\n"
            "Terminal=true\n"
            "Categories=Utility;"
        )
        with open(self.desktop_entry_path, "w") as f:
            f.write(entry)

    def _remove_desktop_entry(self):
        if os.path.exists(self.desktop_entry_path):
            os.remove(self.desktop_entry_path)

    def _set_permissions(self):
        os.chmod(self.install_path, 0o755)

    def _execute_commands_after_update(self):
        subprocess.Popen([self.install_path])

    def _execute_commands_after_install(self):
        subprocess.Popen([self.install_path])