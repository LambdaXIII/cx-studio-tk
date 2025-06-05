from typing import Literal, override
from PIL.Image import Image
from .image_filter import IImageFilter


class SimpleBlackWhiteFilter(IImageFilter):
    def __init__(self):
        super().__init__()

    def run(self, image: Image) -> Image:
        # Convert the image to grayscale (black and white)
        return image.convert("L").convert("RGB")


class TransformColorSpaceFilter(IImageFilter):
    def __init__(self, colorspace: Literal["RGB", "L", "CMYK"]):
        super().__init__()
        self.colorspace = colorspace

    def run(self, image: Image) -> Image:
        if self.colorspace == "RGB" or self.colorspace == "L":
            return image.convert(self.colorspace)
        else:
            return image.convert("RGB").convert(self.colorspace)
