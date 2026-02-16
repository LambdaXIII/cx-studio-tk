from pathlib import Path
from typing import Iterable

from .cx_pathexpander import PathExpander
from .validators import SuffixValidator


class SuffixFinder:
    def __init__(self, *suffixes: str):
        self._suffixes: set[str] = {self.__format_suffix(s) for s in suffixes}

    @staticmethod
    def __format_suffix(suffix: str) -> str:
        suffix = str(suffix).strip().lower()
        if not suffix.startswith("."):
            suffix = "." + suffix
        return suffix

    @property
    def suffixes(self) -> set[str]:
        return self._suffixes

    def add_suffix(self, suffix: str):
        suffix = self.__format_suffix(suffix)
        self._suffixes.add(suffix)

    def remove_suffix(self, suffix: str):
        suffix = self.__format_suffix(suffix)
        self._suffixes.remove(suffix)

    def iter_find(self, path: str | Path, recursive: bool = False) -> Iterable[Path]:
        expander = PathExpander()
        expander.start_info.expand_subdir = recursive
        expander.start_info.accept_files = True
        expander.start_info.accept_dirs = False
        expander.start_info.accept_others = False
        expander.start_info.existed_only = True
        expander.start_info.follow_symlinks = True
        if self._suffixes:
            expander.start_info.file_validator = SuffixValidator(self._suffixes)
        yield from expander.expand(path)
