from pathlib import Path

from .path_validator import IPathValidator
from ...path_utils import is_executable


class ExecutableValidator(IPathValidator):
    def validate(self, path):
        path = Path(path)
        return is_executable(path)
