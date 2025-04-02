from abc import ABC,abstractmethod
from collections.abc import Generator
from io import TextIOBase
from pathlib import PurePath,Path


class IPathProber(ABC):

    @abstractmethod
    def is_acceptable(self,fp:TextIOBase)->bool:
        pass

    @abstractmethod
    def probe(self,fp:TextIOBase)->Generator[PurePath]:
        pass

    @staticmethod
    def _get_suffix(fp:TextIOBase) -> str|None:
        if hasattr(fp,"name"):
            name = Path(fp.name)
            return name.suffix
        return None