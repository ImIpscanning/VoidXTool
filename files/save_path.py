import os
from voidxtool.files.path import VoidXToolPath

class SaveVoidXToolPath:
    @staticmethod
    def save():
        """
        Save the VoidXTool path.
        """
        path_file = os.path.join(VoidXToolPath.get_voidxtool_data_path(), "path")
        with open(path_file, "w") as f:
            f.write(os.getcwd())