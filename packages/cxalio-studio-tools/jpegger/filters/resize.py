from PIL.Image import Image

from .image_filter import IImageFilter


class ResizeFilter(IImageFilter):
    def __init__(self, width: int, height: int):
        super().__init__()
        self.width = width
        self.height = height

    def run(self, image: Image) -> Image:
        w = image.width
        h = image.height
        return image.resize((w, h))


class FactorResizeFilter(IImageFilter):
    def __init__(self, w_factor: float, h_factor: float):
        super().__init__()
        self.w_factor = w_factor
        self.h_factor = h_factor

    def run(self, image: Image) -> Image:
        wf = self.w_factor if self.w_factor > 0 else 1
        hf = self.h_factor if self.h_factor > 0 else 1
        w = image.width * wf
        h = image.height * hf
        return image.resize((w, h))
