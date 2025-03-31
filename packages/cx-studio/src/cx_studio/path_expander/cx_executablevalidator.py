from pathlib import Path

from cx_studio.utils import PathUtils
from .cx_pathvalidator import IPathValidator


class ExecutableValidator(IPathValidator):
    def validate(self, path):
        path = Path(path)
        return PathUtils.is_executable(path)
