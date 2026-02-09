from collections.abc import Collection
from pathlib import Path
from typing import Iterable

from .cx_pathvalidator import *


class SuffixValidator(IPathValidator):
    @staticmethod
    def __clear_suffix(suffix: str) -> str:
        result = suffix.lower()
        if not result.startswith("."):
            result = "." + result
        return result

    def __init__(self, suffixes: Collection | Iterable):
        self.__suffixes = {self.__clear_suffix(str(s)) for s in suffixes}

    def validate(self, path: Path) -> bool:
        return Path(path).suffix.lower() in self.__suffixes
