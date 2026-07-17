"""固定尺寸与比例缩放过滤器。

本模块提供两种低级 resize 过滤器，主要用于需要显式指定像素尺寸
或非等比缩放的场景。日常更推荐 `auto_resize` 中的 `AutoResizeFilter`
与 `AutoScaleFilter`，它们会自动保持宽高比并居中裁剪。
"""

from typing import override

from cx_tools.i18n import _
from PIL.Image import Image

from .image_filter import IImageFilter

__all__ = ["ResizeFilter", "FactorResizeFilter"]


class ResizeFilter(IImageFilter):
    """将图像缩放到固定宽高的过滤器。

    Args:
        width: 目标宽度（像素）。
        height: 目标高度（像素）。
    """

    width: int
    height: int

    def __init__(self, width: int, height: int):
        super().__init__()
        self.width = width
        self.height = height

    @override
    def run(self, image: Image) -> Image:
        """按构造时指定的宽高进行缩放。"""
        return image.resize((self.width, self.height))

    @override
    def __filter_description__(self) -> str:
        """返回描述当前目标尺寸的可读字符串。"""
        return _("将图像分辨率调整为 {width}x{height}").format(
            width=self.width, height=self.height
        )


class FactorResizeFilter(IImageFilter):
    """按水平和垂直比例因子缩放图像的过滤器。

    当某个因子小于等于 0 时，该方向会被视为 1.0（保持原尺寸）。

    Args:
        w_factor: 宽度缩放因子。
        h_factor: 高度缩放因子。
    """

    w_factor: float
    h_factor: float

    def __init__(self, w_factor: float, h_factor: float):
        super().__init__()
        self.w_factor = w_factor
        self.h_factor = h_factor

    @override
    def run(self, image: Image) -> Image:
        """按因子计算目标尺寸并执行 resize。"""
        wf = self.w_factor if self.w_factor > 0 else 1.0
        hf = self.h_factor if self.h_factor > 0 else 1.0
        w = int(image.width * wf)
        h = int(image.height * hf)
        return image.resize((w, h))

    @override
    def __filter_description__(self) -> str:
        """返回描述当前缩放因子的可读字符串。"""
        return _("按宽 {wf}×、高 {hf}× 缩放图像").format(
            wf=f"{self.w_factor:.2f}", hf=f"{self.h_factor:.2f}"
        )
