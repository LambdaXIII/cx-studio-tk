from pathlib import Path

from ...cx_pathutils import is_executable
from .cx_pathvalidator import IPathValidator


class ExecutableValidator(IPathValidator):
    def validate(self, path):
        path = Path(path)
        return is_executable(path)
