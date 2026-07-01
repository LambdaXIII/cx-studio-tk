"""标签渲染协议。"""

from __future__ import annotations

from collections.abc import Generator, Iterable
from typing import Any, Literal

from rich.console import RenderableType
from rich.text import Text

__all__ = ["RichLabelMixin", "RichLabel"]


class RichLabelMixin:
    """标签渲染协议 mixin。

    子类实现 __rich_label__() 后，本 mixin 自动提供 __rich__()
    默认实现，使 console.print(obj) 直接输出标签渲染。

    若子类自行实现 __rich__()，则覆盖 mixin 默认实现。
    """

    def __rich_label__(self) -> Generator[RenderableType, None, None]:
        """yield 标签片段。子类必须实现此方法。"""
        raise NotImplementedError

    def __rich__(self) -> RenderableType:
        """默认渲染：调用 __rich_label__() 并组装为 Text。"""
        return _render_label(self)


class RichLabel:
    """标签包装器，用于不愿继承 RichLabelMixin 的对象。

    与 RichLabelMixin.__rich__ 共享同一套渲染逻辑（_render_label）。
    """

    def __init__(
        self,
        obj: Any,
        *,
        markup: bool = True,
        sep: str = " ",
        tab_size: int = 1,
        overflow: Literal["ignore", "crop", "ellipsis", "fold"] = "crop",
        justify: Literal["left", "center", "right"] = "left",
    ) -> None:
        self.obj = obj
        self.markup = markup
        self.sep = sep
        self.tab_size = tab_size
        self.overflow = overflow
        self.justify = justify

    def __rich__(self) -> RenderableType:
        return _render_label(
            self.obj,
            markup=self.markup,
            sep=self.sep,
            tab_size=self.tab_size,
            overflow=self.overflow,
            justify=self.justify,
        )


def _iter_with_separator(
    items: Iterable[RenderableType], sep: str
) -> Generator[RenderableType, None, None]:
    """在迭代项之间插入分隔符，不在末尾添加。"""
    it = iter(items)
    try:
        prev = next(it)
    except StopIteration:
        return
    yield prev
    for item in it:
        yield sep
        yield item


def _fragment_to_text(fragment: Any, markup: bool) -> Text:
    """将单个标签片段转换为 Text。

    - str：按 markup 参数决定是否解析为 Rich markup
    - Text：保持原样
    - 其他可渲染对象：退化为纯文本字符串
    """
    if isinstance(fragment, str):
        return Text.from_markup(fragment) if markup else Text(fragment)
    if isinstance(fragment, Text):
        return fragment
    return Text(str(fragment))


def _render_label(
    obj: Any,
    *,
    markup: bool = True,
    sep: str = " ",
    tab_size: int = 1,
    overflow: Literal["ignore", "crop", "ellipsis", "fold"] = "crop",
    justify: Literal["left", "center", "right"] = "left",
) -> Text:
    """标签渲染核心逻辑。

    1. 调用 obj.__rich_label__() 获取片段生成器
    2. 用 sep 在片段间插入分隔符（iter_with_separator 内联实现）
    3. 组装为 rich.Text（支持 markup、overflow、justify）
    4. tab_size 交由 Text 处理制表符宽度
    """
    label_method = getattr(obj, "__rich_label__", None)
    if label_method is None or not callable(label_method):
        raise TypeError(
            f"{type(obj).__name__!r} object has no callable __rich_label__ method"
        )

    fragments = obj.__rich_label__()
    text = Text(
        tab_size=tab_size,
        overflow=overflow,
        justify=justify,
    )
    for fragment in _iter_with_separator(fragments, sep):
        text.append(_fragment_to_text(fragment, markup))
    return text
