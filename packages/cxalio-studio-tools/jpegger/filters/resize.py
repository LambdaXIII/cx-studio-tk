from PIL.Image import Image
from .image_filter import IImageFilter


class ResizeFilter(IImageFilter):
    def __init__(self, width: int, height: int):
        super().__init__()
        self.width = width
        self.height = height

    def run(self, image: Image) -> Image:
        w = image.width if image.width > 0 else image.width
        h = image.height if image.height > 0 else image.height
        return image.resize((w, h))


class FactorResizeFilter(IImageFilter):
    def __init__(self, w_factor: float, h_factor: float):
        super().__init__()
        self.w_factor = w_factor
        self.h_factor = h_factor

    def run(self, image: Image) -> Image:
        wf = self.w_factor if self.w_factor > 0 else 1
        wh = self.h_factor if self.h_factor > 0 else 1
        w = image.width * wf
        h = image.height * wh
        return image.resize((w, h))


class ScaleAndCropFilter(IImageFilter):
    def __init__(self, width: int, height: int):
        super().__init__()
        self.width = width
        self.height = height

    def run(self, image: Image) -> Image:
        iw, ih = image.size
        if self.width >= self.height:
            factor = self.width / iw
            scaled_image = image.resize((self.width, int(ih * factor)))
            y = (scaled_image.height - self.height) / 2
            return scaled_image.crop((0, y, self.width, y + self.height))
        else:
            factor = self.height / ih
            scaled_image = image.resize((int(iw * factor), self.height))
            x = (scaled_image.width - self.width) / 2
            return scaled_image.crop((x, 0, x + self.width, self.height))
