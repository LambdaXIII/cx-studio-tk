from abc import ABC, abstractmethod
from enum import Enum

from rich.console import Console


class IAppEnvironment(ABC):
    def __init__(self):
        self.app_name = ""
        self.app_version = ""
        self.console = Console(stderr=True)

    @abstractmethod
    def is_debug_mode_on(self):
        return False

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

    def say(self, *args, **kwargs):
        self.console.print(*args, **kwargs)

    def whisper(self, *args, **kwargs):
        if self.is_debug_mode_on():
            kwargs["style"] = "dim"
            kwargs["highlight"] = False
            self.console.print(*args, **kwargs)
