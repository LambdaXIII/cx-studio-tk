from abc import ABC, abstractmethod
from PIL.Image import Image


class IImageFilter(ABC):
    @abstractmethod
    def run(self, image: Image) -> Image:
        pass

    def filter_name(self):
        return self.__class__.__name__.replace("Filter", "")

    def __rich_label__(self):
        yield f"[yellow]{self.filter_name()}[/yellow]"
