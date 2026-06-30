"""色彩空间转换过滤器。

目前提供两种实现：
- `ColorSpaceFilter`: 标准色彩空间转换，可输出 RGB / L / CMYK。
- `SimpleBlackWhiteFilter`: 先转灰度（L）再回 RGB，用于需要保留
  RGB 三通道但内容是黑白效果的场景。
"""

from collections.abc import Generator
from typing import override

from cx_tools.i18n import _
from PIL.Image import Image

from .image_filter import IImageFilter


class SimpleBlackWhiteFilter(IImageFilter):
    """简单黑白效果过滤器。

    先将图像转换为灰度（L），再转回 RGB，使结果仍保持 3 通道。
    """

    def __init__(self):
        super().__init__()

    @override
    def run(self, image: Image) -> Image:
        """将图像转换为灰度后再转回 RGB。"""
        return image.convert("L").convert("RGB")

    @override
    def __rich_label__(self) -> Generator[str, None, None]:
        """在标签中显示 L→RGB 转换标识。"""
        yield from super().__rich_label__()
        yield "[blue](L→RGB)[/]"

    @override
    def __filter_description__(self) -> str:
        """返回过滤器描述。"""
        return _("将图像转换为灰度（L）后再回 RGB 表示")


class ColorSpaceFilter(IImageFilter):
    """标准色彩空间转换过滤器。

    支持的色彩空间由命令行参数限定为 "RGB"、"L"、"CMYK"。
    当目标为 CMYK 时，会先将图像转到 RGB 再转 CMYK，以减少
    非标准输入模式导致的异常。

    Args:
        colorspace: 目标色彩空间字符串，可为空（不处理）。
    """

    colorspace: str | None

    def __init__(self, colorspace: str | None):
        super().__init__()
        self.colorspace = colorspace

    @override
    def run(self, image: Image) -> Image:
        """按目标色彩空间转换图像。"""
        if not self.colorspace:
            return image
        if self.colorspace == "RGB" or self.colorspace == "L":
            return image.convert(self.colorspace)
        else:
            return image.convert("RGB").convert(self.colorspace)

    @override
    def __rich_label__(self) -> Generator[str, None, None]:
        """使用彩色块直观展示目标色彩空间。"""
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

    @override
    def __filter_description__(self) -> str:
        """返回描述目标色彩空间的可读字符串。"""
        return _("将图像的色彩空间转换为 {space}").format(
            space=self.colorspace or _("默认")
        )
