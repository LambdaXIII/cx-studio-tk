from pathlib import Path

from .cx_pathvalidator import *


class SuffixValidator(IPathValidator):
    @staticmethod
    def __clear_suffix(suffix: str) -> str:
        result = suffix.lower()
        if not result.startswith("."):
            result = "." + result
        return result

    def __init__(self, suffixes: list[str]):
        if not isinstance(suffixes, list):
            suffixes = [suffixes]
        self.__suffixes = {self.__clear_suffix(s) for s in suffixes}

    def validate(self, path: Path) -> bool:
        return Path(path).suffix.lower() in self.__suffixes
