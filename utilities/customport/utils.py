from rich.console import Console
from ezjsonpy import get_config_value, set_config_value, remove_config_value, config_value_exists
from voidxtool.constants import VoidXToolConstants
from voidxtool.utilities.input import Input
from voidxtool.gui.language import Msg

console: Console = Console()

class CustomPortsUtils:
    __firstlineno__ = 11
    COMMAND_NAME: str = 'customport'

    @staticmethod
    def add_customport():
        """
        Method to add a customport.
        """
        customport_name = Input.get_input(
            Msg.get(f"commands.{CustomPortsUtils.COMMAND_NAME}.messages.customportName"),
            input_type="string"
        )
        if not customport_name:
            return None
        customport_range = Input.get_input(
            Msg.get(f"commands.{CustomPortsUtils.COMMAND_NAME}.messages.customportRange"),
            input_type="string"
        )
        if not customport_range:
            return None
        customports = get_config_value("customports") or []
        for port in customports:
            if port["range"] == customport_range:
                msg = Msg.get(f"commands.{CustomPortsUtils.COMMAND_NAME}.messages.customportRangeAlreadyExists")
                msg = msg.replace("%customportRange%", customport_range)
                console.print(msg)
                return None
        customports.append({"name": customport_name, "range": customport_range})
        set_config_value("customports", customports)
        msg = Msg.get(f"commands.{CustomPortsUtils.COMMAND_NAME}.messages.customportAdded")
        msg = msg.replace("%customport%", customport_name)
        console.print(msg)
        return True

    @staticmethod
    def remove_customport():
        """
        Method to remove a customport.
        """
        customport_range = Input.get_input(
            Msg.get(f"commands.{CustomPortsUtils.COMMAND_NAME}.messages.customportRange"),
            input_type="string"
        )
        if not customport_range:
            return None
        customports = get_config_value("customports") or []
        new_customports = [port for port in customports if port["range"] != customport_range]
        if len(new_customports) == len(customports):
            return None
        set_config_value("customports", new_customports)
        msg = Msg.get(f"commands.{CustomPortsUtils.COMMAND_NAME}.messages.customportRemoved")
        msg = msg.replace("%customportRange%", customport_range)
        console.print(msg)
        return True

    @staticmethod
    def list_customports() -> bool:
        """
        List all customports.
        """
        customports = get_config_value("customports") or []
        if not customports:
            console.print(VoidXToolConstants.INFO_PREFIX + " No customports found.")
            return False
        for port in customports:
            console.print(f"[bold green]{port['name']}[/bold green]: [yellow]{port['range']}[/yellow]")
        return True

    __static_attributes__ = ()