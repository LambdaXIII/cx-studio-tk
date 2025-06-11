from abc import ABC, abstractmethod
from PIL.Image import Image


class IImageFilter(ABC):

    @abstractmethod
    def run(self, image: Image) -> Image:
        pass

    def __rich_label__(self) -> str:
        name = self.__class__.__name__
        name.replace("Filter", "")
        return f"[yellow]{name}[/yellow]"
