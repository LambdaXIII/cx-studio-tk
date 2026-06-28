import sys
from abc import ABC, abstractmethod
from typing import Self
from collections.abc import Sequence


class IApplication(ABC):
    def __init__(self, arguments: Sequence[str] | None = None) -> None:
        self.sys_arguments = arguments or sys.argv[1:]

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        self.stop()
        return False

    @abstractmethod
    def run(self) -> None:
        pass
