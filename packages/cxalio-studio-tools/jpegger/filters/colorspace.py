from typing import Literal, override
from PIL.Image import Image
from pytest import param
from .image_filter import IImageFilter


class SimpleBlackWhiteFilter(IImageFilter):
    def __init__(self):
        super().__init__()

    def run(self, image: Image) -> Image:
        # Convert the image to grayscale (black and white)
        return image.convert("L").convert("RGB")


class ColorSpaceFilter(IImageFilter):
    colorspace_type = Literal["RGB", "L", "CMYK"]

    def __init__(self, colorspace: str | None):
        super().__init__()
        self.colorspace = colorspace

    def run(self, image: Image) -> Image:
        if not self.colorspace:
            return image
        if self.colorspace == "RGB" or self.colorspace == "L":
            return image.convert(self.colorspace)
        else:
            return image.convert("RGB").convert(self.colorspace)

    def __rich_label__(self):
        yield from super().__rich_label__()
        _RGB = "[black on red]R[black on green]G[black on blue]B[reset]"
        _CMYK = "[black on cyan]C[black on magenta]M[black on yellow]Y[black on black]K[reset]"
        _L = "[black on white]L[reset]"
        _NONE = "[red]N/A[/]"
        param = {
            "RGB": _RGB,
            "CMYK": _CMYK,
            "L": _L,
            None: _NONE,
        }.get(self.colorspace, _NONE)
        yield f"[blue]({param})[/]"

    def __filter_description__(self) -> str:
        return f"将图像的色彩空间转换为 {self.colorspace}"
