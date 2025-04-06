from abc import ABC, abstractmethod
from collections.abc import Generator
from io import TextIOBase
from pathlib import PurePath, Path


class IPathProber(ABC):
    class ProbeGuard:
        def __init__(self, fp: TextIOBase):
            self.__fp = fp
            self.__location = fp.tell()
            self.__cache = set()

        def reset(self):
            self.__fp.seek(self.__location)
            self.__cache.clear()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.reset()
            return False

        def is_new(self, x: PurePath | str) -> bool:
            s = str(x)
            contains = s in self.__cache
            self.__cache.add(s)
            return not contains

        def seek(self, x: int = 0):
            self.__fp.seek(x)

    @abstractmethod
    def _is_acceptable(self, fp: TextIOBase) -> bool:
        pass

    @abstractmethod
    def _probe(self, fp: TextIOBase) -> Generator[PurePath]:
        pass

    def is_acceptable(self, fp: TextIOBase) -> bool:
        try:
            return self._is_acceptable(fp)
        except UnicodeDecodeError:
            return False

    def probe(self, fp: TextIOBase) -> Generator[PurePath]:
        try:
            yield from self._probe(fp)
        except UnicodeDecodeError:
            pass

    def pre_check(self, filename: str | Path)->bool:
        _ = self
        return True

    @staticmethod
    def _get_suffix(fp: TextIOBase) -> str | None:
        if hasattr(fp, "name"):
            name = Path(getattr(fp, "name"))
            return name.suffix
        return None

    @staticmethod
    def _get_lines(fp: TextIOBase, max_lines: int = 10) -> Generator[str]:
        for line in fp:
            if len(line) == 0:
                continue
            yield line
            max_lines -= 1
            if max_lines <= 0:
                break
