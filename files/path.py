import os
from loguru import logger

class VoidXToolPath:
    @staticmethod
    def get_voidxtool_installed_path() -> str:
        """
        Get the path of the VoidXTool before installation.

        :return: The path of the VoidXTool before installation.
        """
        folder_name = "VoidXTool"
        if os.name == "nt":
            return os.path.abspath(os.path.join(os.getenv("APPDATA"), folder_name))
        else:
            return os.path.abspath(os.path.join(os.getenv("HOME"), ".config", folder_name))

    @staticmethod
    def get_voidxtool_data_path() -> str:
        """
        Get the path of the VoidXTool files.

        :return: The path of the VoidXTool files.
        """
        folder_name = "VoidXToolData"
        if os.name == "nt":
            path = os.path.abspath(os.path.join(os.getenv("APPDATA"), folder_name))
        else:
            path = os.path.abspath(os.path.join(os.getenv("HOME"), ".config", folder_name))
        if not os.path.exists(path):
            logger.info(f"Creating VoidXTool files folder at {path}")
            os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def get_voidxtool_path() -> str:
        """
        Get the path of the VoidXTool.

        :return str: The path of the VoidXTool.
        """
        return os.getcwd()