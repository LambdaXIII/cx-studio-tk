from .image_filter import IImageFilter

from PIL.Image import Image

__all__ = ["AutoResizeFilter", "AutoScaleFilter"]


def _auto_resize(image: Image, width: int, height: int) -> Image:
    iw, ih = image.size
    if (width, height) == (iw, ih):
        return image

    if width >= height:
        _factor = width / iw
        scaled_image = image.resize((width, int(ih * _factor)))
        y = (scaled_image.height - height) / 2
        return scaled_image.crop((0, y, width, y + height))
    else:
        _factor = height / ih
        scaled_image = image.resize((int(iw * _factor), height))
        x = (scaled_image.width - width) / 2
        return scaled_image.crop((x, 0, x + width, height))


class AutoResizeFilter(IImageFilter):
    """Auto resize filter
    Resize image to fit the given width and height.

    If `width` and `height` are both None, the image will be resized to a fixed size.
    If `width` or `height` is None, the resized image will keep the aspect ratio.
    If `width` and `height` are both not None, the image remains.

    **No matter how the resizing is done,
    the image will be cropped to fit the given size and positioned in the center.**

    Parameters
    width: int | None
        The width of the resized image.
    height: int | None
        The height of the resized image.
    """

    def __init__(self, width: int | None = None, height: int | None = None):
        super().__init__()
        self.width = None if width is None or width <= 0 else width
        self.height = None if height is None or height <= 0 else height

    def get_target_size(self, image: Image) -> tuple[int, int]:
        if self.width and self.height:
            target_width, target_height = self.width, self.height
        elif self.width and not self.height:
            target_width = self.width
            factor = target_width / image.width
            target_height = int(image.height * factor)
        elif self.height and not self.width:
            target_height = self.height
            factor = target_height / image.height
            target_width = int(image.width * factor)
        else:
            target_width, target_height = image.width, image.height

        return target_width, target_height

    def run(self, image: Image) -> Image:
        iw, ih = self.get_target_size(image)
        return _auto_resize(image, iw, ih)

    def __rich_label__(self) -> str:
        parameter = (
            f"[blue][[u]{self.width or "N/A"}{":" if self.height else ""}{self.height or "N/A"}[/u]][/blue]"
            if self.width or self.height
            else ""
        )
        return f"[yellow]AutoResize[/]{parameter}"


class AutoScaleFilter(IImageFilter):
    """AutoScaleFilter

    Same as AutoResizeFilter, but uses a factor instead of a size.
    ** If the size is 1.0 or negative, the imgae remains.**
    """

    def __init__(self, factor: float = 1.0):
        super().__init__()
        self.factor = factor

    def get_target_size(self, image: Image) -> tuple[int, int]:
        iw, ih = image.width, image.height
        if self.factor <= 0 or self.factor == 1.0:
            return iw, ih

        target_width = int(iw * self.factor)
        target_height = int(ih * self.factor)
        return target_width, target_height

    def run(self, image: Image) -> Image:
        iw, ih = self.get_target_size(image)
        return _auto_resize(image, iw, ih)

    def __rich_label__(self) -> str:
        parameter = f"[blue][[u]{self.factor:.2f}[/u]][/]"
        return f"[yellow]AutoScale[/]{parameter}"
