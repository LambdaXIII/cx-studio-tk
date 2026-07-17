"""自动保持比例并居中裁剪的缩放过滤器。

`AutoResizeFilter` 与 `AutoScaleFilter` 都基于 `_auto_resize` 实现：
先按较短边等比放大到目标尺寸，再沿较长边居中裁剪，确保输出
严格为指定尺寸。
"""

from collections.abc import Generator
from typing import Literal, override

from cx_tools.i18n import _
from PIL.Image import Image

from .image_filter import IImageFilter

__all__ = ["AutoResizeFilter", "AutoScaleFilter"]

ResizingMode = Literal["fixed", "width_fixed", "height_fixed", "remains"]


def _auto_resize(image: Image, width: int, height: int) -> Image:
    """将图像等比缩放并居中裁剪到指定尺寸。

    该函数按较短边方向先 scale 到目标边长，再在较长边方向
    居中裁剪，保证输出严格为 `(width, height)`。

    Args:
        image: 源图像。
        width: 目标宽度。
        height: 目标高度。

    Returns:
        缩放并裁剪后的图像。
    """
    iw, ih = image.size
    if (width, height) == (iw, ih):
        return image

    if iw <= ih:
        _factor = width / iw
        scaled_image = image.resize((width, int(ih * _factor)))
        y = int((scaled_image.height - height) / 2)
        return scaled_image.crop((0, y, width, y + height))
    else:
        _factor = height / ih
        scaled_image = image.resize((int(iw * _factor), height))
        x = int((scaled_image.width - width) / 2)
        return scaled_image.crop((x, 0, x + width, height))


class AutoResizeFilter(IImageFilter):
    """自动 resize 过滤器。

    根据给定的宽度和高度调整图像尺寸，并保持原图比例后居中裁剪。

    - 若 `width` 和 `height` 均指定，输出严格为此尺寸。
    - 若只指定 `width`，高度按原比例等比缩放。
    - 若只指定 `height`，宽度按原比例等比缩放。
    - 若均未指定（或均 <= 0），不对图像做任何处理。

    Args:
        width: 目标宽度，None 或 <= 0 表示不固定。
        height: 目标高度，None 或 <= 0 表示不固定。
    """

    _width: int | None
    _height: int | None

    def __init__(self, width: int | None = None, height: int | None = None):
        super().__init__()
        self._width = None if width is None or width <= 0 else width
        self._height = None if height is None or height <= 0 else height

    @property
    def resizing_mode(self) -> ResizingMode:
        """返回当前的缩放模式。"""
        if self._width and self._height:
            return "fixed"
        elif self._width and not self._height:
            return "width_fixed"
        elif self._height and not self._width:
            return "height_fixed"
        return "remains"

    def get_target_size(self, image: Image) -> tuple[int, int]:
        """根据缩放模式与源图像尺寸计算目标尺寸。

        Args:
            image: 源图像。

        Returns:
            (目标宽度, 目标高度)。
        """
        target_width, target_height = iw, ih = image.size
        match self.resizing_mode:
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
            case _:
                pass
        assert target_width
        assert target_height
        return target_width, target_height

    @override
    def run(self, image: Image) -> Image:
        """执行自动缩放并居中裁剪。"""
        iw, ih = self.get_target_size(image)
        return _auto_resize(image, iw, ih)

    @override
    def __rich_label__(self) -> Generator[str, None, None]:
        """在标签中显示目标宽高。"""
        na = "[red]N/A[/red]"
        yield from super().__rich_label__()
        yield f"[blue]({self._width or na}:{self._height or na})[/]"

    @override
    def __filter_description__(self) -> str:
        """返回描述当前缩放行为的可读字符串。"""
        match self.resizing_mode:
            case "fixed":
                return _("调整图像分辨率至 {width}x{height}").format(
                    width=self._width, height=self._height
                )
            case "width_fixed":
                return _("将图像宽度调整为 {width}，并保持原图比例缩放高度").format(
                    width=self._width
                )
            case "height_fixed":
                return _("将图像高度调整为 {height}，并保持原图比例缩放宽度").format(
                    height=self._height
                )
            case _:
                pass
        return _("不对图像做任何处理")


class AutoScaleFilter(IImageFilter):
    """按比例因子自动缩放过滤器。

    与 `AutoResizeFilter` 类似，但以单一比例因子控制输出尺寸。
    当因子 <= 0 或等于 1.0 时，图像保持原尺寸。

    Args:
        factor: 缩放因子。
    """

    factor: float

    def __init__(self, factor: float = 1.0):
        super().__init__()
        self.factor = factor

    def get_target_size(self, image: Image) -> tuple[int, int]:
        """按因子计算目标尺寸。

        Args:
            image: 源图像。

        Returns:
            (目标宽度, 目标高度)。
        """
        iw, ih = image.width, image.height
        if self.factor <= 0 or self.factor == 1.0:
            return iw, ih

        target_width = int(iw * self.factor)
        target_height = int(ih * self.factor)
        return target_width, target_height

    @override
    def run(self, image: Image) -> Image:
        """执行比例缩放。"""
        iw, ih = self.get_target_size(image)
        return _auto_resize(image, iw, ih)

    @override
    def __rich_label__(self) -> Generator[str, None, None]:
        """在标签中显示缩放因子。"""
        yield from super().__rich_label__()
        yield f"[blue]({self.factor:.2f}x)[/]"

    @override
    def __filter_description__(self) -> str:
        """返回描述当前缩放行为的可读字符串。"""
        if self.factor == 1.0 or self.factor <= 0:
            return _("不对图像做任何处理")
        return _("将图像宽度和高度缩放 {factor} 倍").format(factor=f"{self.factor:.2f}")
