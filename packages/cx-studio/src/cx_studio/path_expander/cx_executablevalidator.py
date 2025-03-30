from .cx_pathvalidator import IPathValidator
from pathlib import Path
from cx_studio.utils import PathUtils


class ExecutableValidator(IPathValidator):
    def validate(self, path):
        path = Path(path)
        return PathUtils.is_excutable(path)
