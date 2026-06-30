"""图像过滤器链。

`ImageFilterChain` 本身也实现 `IImageFilter`，因此可以嵌套组合。
链中的过滤器按添加顺序依次作用于 PIL `Image` 实例。
"""

from collections.abc import Generator, Sequence
from typing import override

from PIL.Image import Image

from .image_filter import IImageFilter


class ImageFilterChain(IImageFilter):
    """按顺序执行多个 `IImageFilter` 的过滤器链。

    Args:
        filters: 初始过滤器序列；内部会复制为列表，避免外部修改。
    """

    filters: list[IImageFilter]

    def __init__(self, filters: Sequence[IImageFilter]):
        super().__init__()
        self.filters = list(filters)

    def append(self, img_filter: IImageFilter) -> None:
        """向链尾追加一个过滤器。

        若追加对象本身也是 `ImageFilterChain`，则将其内部过滤器
        平铺展开后追加，避免链套链带来的层级噪音。

        Args:
            img_filter: 要追加的过滤器实例。
        """
        if isinstance(img_filter, ImageFilterChain):
            self.filters.extend(img_filter.filters)
        else:
            self.filters.append(img_filter)

    @override
    def run(self, image: Image) -> Image:
        """依次执行链中所有过滤器。"""
        for img_filter in self.filters:
            image = img_filter.run(image)
        return image

    @override
    def filter_name(self) -> str:
        """链的显示名称固定为 "FilterChain"。"""
        return "FilterChain"

    def __len__(self) -> int:
        """返回链中过滤器数量。"""
        return len(self.filters)

    @override
    def __rich_label__(self) -> Generator[str, None, None]:
        """在标签中显示链及过滤器数量。"""
        yield from super().__rich_label__()
        yield f"[blue]({len(self.filters)}Filters)[/]"

    def __rich_detail__(self) -> Generator[tuple[str, str], None, None]:
        """为详情面板列出每一步过滤器及其描述。"""
        for i, f in enumerate(self.filters):
            yield f"[cyan]#{i} {f.filter_name()}[/]", f.__filter_description__()

    @override
    def __filter_description__(self) -> str:
        """返回所有过滤器描述的分号拼接字符串。"""
        descriptions = [f.__filter_description__() for f in self.filters]
        return ";".join(descriptions)

    def step_descriptions(self) -> list[str]:
        """返回 "FilterName:description" 形式的步骤列表。"""
        return [f"{f.filter_name()}:{f.__filter_description__()}" for f in self.filters]

    def __rich_repr__(self) -> Generator[tuple[str, str], None, None]:
        """为 Rich 渲染提供 `(key, value)` 形式的元组。"""
        for i, f in enumerate(self.filters):
            yield f"{i}:{f.filter_name()}", f.__filter_description__()
