import sys
from abc import ABC, abstractmethod
from collections.abc import Sequence


class IApplication(ABC):
    def __init__(self, arguments: Sequence[str] | None = None):
        self.sys_arguments = arguments or sys.argv[1:]

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    @abstractmethod
    def run(self):
        pass
