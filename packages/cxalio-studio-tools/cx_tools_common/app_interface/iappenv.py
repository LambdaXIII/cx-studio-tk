from abc import ABC,abstractmethod
from enum import Enum

from rich.console import Console

class IAppEnvironment(ABC):
    def __init__(self):
        self.app_name = ""
        self.app_version = ""
        self.console = Console(stderr=True)
        self.debug_console = Console(stderr=True,style="bright black")
        self.debug_mode = False

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

    def print(self,*args,**kwargs):
        self.console.print(*args,**kwargs)

    def debug(self,*args,**kwargs):
        if self.debug_mode:
            self.debug_console.print(*args,**kwargs)




