from pathlib import Path

from .cx_pathvalidator import IPathValidator
from ...cx_pathutils import is_executable


class ExecutableValidator(IPathValidator):
    def validate(self, path):
        path = Path(path)
        return is_executable(path)
