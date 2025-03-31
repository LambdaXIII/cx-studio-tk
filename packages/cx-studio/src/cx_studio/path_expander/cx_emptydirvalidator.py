from pathlib import Path

from .cx_pathvalidator import IPathValidator


class EmptyDirValidator(IPathValidator):

    def __init__(self, reverse=False):
        self.__reverse = reverse

    def validate(self, path: Path) -> bool:
        if not path.is_dir():
            return False
        is_empty = len(list(path.iterdir())) == 0
        return not is_empty if self.__reverse else is_empty
