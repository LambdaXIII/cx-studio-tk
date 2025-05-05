from abc import ABC, abstractmethod


class IHostProvider(ABC):
    @abstractmethod
    def list_id(self):
        pass
