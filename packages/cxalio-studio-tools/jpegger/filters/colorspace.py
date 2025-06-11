from typing import Literal, override
from PIL.Image import Image
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

    def __rich_label__(self) -> str:
        param = ""
        match (self.colorspace):
            case "RGB":
                param = "[red]R[/][green]G[/][blue]B[/]"
            case "L":
                param = "[white]L[/]"
            case "CMYK":
                param = "[cyan]C[/][magenta]M[/][yellow]Y[/][black]K[/]"
            case _:
                param = "[red]N/A[/]"

        return f"[yellow]ColorSpace[/][blue][[u]{param}[/]][/]"
