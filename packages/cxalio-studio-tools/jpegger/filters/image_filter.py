from abc import ABC, abstractmethod
from PIL.Image import Image


class IImageFilter(ABC):

    @abstractmethod
    def run(self, image: Image) -> Image:
        pass
