from .iappenv import IAppEnvironment


from abc import ABC,abstractmethod


class IApplication(ABC):

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

