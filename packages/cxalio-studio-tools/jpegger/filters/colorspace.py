from PIL.Image import Image
from .image_filter import IImageFilter


class SimpleBlackWhiteFilter(IImageFilter):
    def __init__(self):
        super().__init__()

    def run(self, image: Image) -> Image:
        # Convert the image to grayscale (black and white)
        return image.convert("L").convert("RGB")
