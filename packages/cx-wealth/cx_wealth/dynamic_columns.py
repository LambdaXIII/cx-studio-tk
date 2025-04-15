from collections.abc import Sequence, Iterable, Generator

from . import rich_types as r


class DynamicColumns:
    """动态列渲染器，根据终端宽度自动调整列数和列宽。

    将一组渲染对象按列布局显示，最多显示指定的最大列数。当对象数量超过最大列数时，
    每列宽度会根据终端宽度平均分配；若对象数量不足，则按单列自适应显示。支持扩展填充终端可用空间。

    Args:
        renderables (Sequence | Iterable): 要渲染的对象集合。
        max_columns (int, optional): 允许的最大列数，默认为2。
        expand (bool, optional): 是否扩展填充终端宽度，默认为True。
    """

    def __init__(
        self, renderables: Sequence | Iterable, max_columns: int = 2, expand=True
    ):
        self._renderables = list(renderables)
        self._max_columns = max_columns
        self._expand = expand

    def __rich_console__(
        self, console: r.Console, _options: r.ConsoleOptions
    ) -> "Generator[r.RenderableType, None, None]":
        """Rich库渲染钩子，生成列式布局的渲染对象。

        Args:
            console (rich.Console): 当前控制台实例。
            _options (rich.ConsoleOptions): 渲染选项（未使用）。

        Yields:
            rich.Columns: 根据终端宽度计算后的列式布局对象。
        """
        w = (
            None
            if len(self._renderables) < self._max_columns
            else int(console.width / self._max_columns) - 1
        )
        yield r.Columns(
            self._renderables, expand=self._expand, equal=True, width=w
        )