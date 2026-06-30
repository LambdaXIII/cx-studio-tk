"""图像过滤器的抽象接口。

该模块定义了 Jpegger 图像处理流水线的核心契约：所有具体过滤器
都必须实现 `IImageFilter`，并通过 `run()` 对 PIL `Image` 实例进行
转换。类名中的 "Filter" 后缀会在 `filter_name()` 中被自动去除，
用于生成更紧凑的 Rich 标签。
"""

from abc import ABC, abstractmethod
from collections.abc import Generator

from PIL.Image import Image


class IImageFilter(ABC):
    """图像过滤器的抽象基类。

    所有图像处理步骤（缩放、裁剪、色彩空间转换等）都应通过实现
    该接口嵌入 `ImageFilterChain` 中。
    """

    @abstractmethod
    def run(self, image: Image) -> Image:
        """对输入图像执行过滤并返回处理后的图像。

        Args:
            image: 待处理的 PIL 图像实例。

        Returns:
            处理后的 PIL 图像实例。
        """
        ...

    def filter_name(self) -> str:
        """返回过滤器的简短显示名称（去掉类名中的 "Filter" 后缀）。"""
        return self.__class__.__name__.replace("Filter", "")

    @abstractmethod
    def __filter_description__(self) -> str:
        """返回过滤器的可读描述，用于详情面板与日志。"""
        ...

    def __rich_label__(self) -> Generator[str, None, None]:
        """为 `WealthLabel` 提供紧凑标签片段。

        Yields:
            可渲染字符串或 Rich 对象片段。
        """
        yield f"[yellow]{self.filter_name()}[/yellow]"
