from typing import Literal

from PIL.Image import Image

from .image_filter import IImageFilter

__all__ = ["AutoResizeFilter", "AutoScaleFilter"]


def _auto_resize(image: Image, width: int, height: int) -> Image:
    iw, ih = image.size
    if (width, height) == (iw, ih):
        return image

    if iw <= ih:
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

    ResizingMode = Literal["fixed", "width_fixed", "height_fixed", "remains"]

    def __init__(self, width: int | None = None, height: int | None = None):
        super().__init__()
        self._width = None if width is None or width <= 0 else width
        self._height = None if height is None or height <= 0 else height

    @property
    def resizing_mode(self) -> ResizingMode:
        if self._width and self._height:
            return "fixed"
        elif self._width and not self._height:
            return "width_fixed"
        elif self._height and not self._width:
            return "height_fixed"
        return "remains"

    def get_target_size(self, image: Image) -> tuple[int, int]:
        target_width, target_height = iw, ih = image.size
        match (self.resizing_mode):
            case "fixed":
                target_width, target_height = self._width, self._height
            case "width_fixed":
                assert self._width
                target_width = self._width
                ratio = target_width / iw
                target_height = int(ih * ratio)
            case "height_fixed":
                assert self._height
                target_height = self._height
                ratio = target_height / ih
                target_width = int(iw * ratio)
        assert target_width
        assert target_height
        return target_width, target_height

    def run(self, image: Image) -> Image:
        iw, ih = self.get_target_size(image)
        return _auto_resize(image, iw, ih)

    def __rich_label__(self):
        na = "[red]N/A[/red]"
        yield super().__rich_label__()
        yield f"[blue]({self._width or na}:{self._height or na})[/]"

    def __filter_description__(self) -> str:
        match (self.resizing_mode):
            case "fixed":
                return f"调整图像分辨率至 {self._width}x{self._height}"
            case "width_fixed":
                return f"将图像宽度调整为 {self._width} ，并保持原图比例缩放高度"
            case "height_fixed":
                return f"将图像高度调整为 {self._height} ，并保持原图比例缩放宽度"
        return "不对图像做任何处理"


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

    def __rich_label__(self):
        yield from super().__rich_label__()
        yield f"[blue]({self.factor:.2f}x)[/]"

    def __filter_description__(self) -> str:
        if self.factor == 1.0 or self.factor <= 0:
            return "不对图像做任何处理"
        return f"将图像宽度和高度缩放 {self.factor:.2f} 倍"
