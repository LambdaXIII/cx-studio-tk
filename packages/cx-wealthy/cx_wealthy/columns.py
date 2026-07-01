"""固定最大列数的多列布局组件。"""

from __future__ import annotations

from collections.abc import Generator, Iterable

from rich.console import Console, ConsoleOptions, Group, RenderableType
from rich.table import Table
from rich.text import Text

__all__ = ["MaxColumnsLayout"]


class MaxColumnsLayout:
    """固定最大列数的多列布局。

    诚实命名：按最大列数平均分配宽度，不做基于内容的动态测量。
    """

    def __init__(
        self,
        renderables: Iterable[RenderableType],
        *,
        max_columns: int = 2,
        expand: bool = True,
        column_gap: int = 1,
    ) -> None:
        """
        Args:
            renderables: 要渲染的对象集合
            max_columns: 允许的最大列数
            expand: 是否扩展填充终端宽度
            column_gap: 列间距
        """
        self._renderables = list(renderables)
        self._max_columns = max_columns
        self._expand = expand
        self._column_gap = column_gap

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> Generator[RenderableType, None, None]:
        """标准 Rich 渲染钩子（yield 范式）。

        Args:
            console: 当前控制台实例
            options: 渲染选项

        Yields:
            按列布局的 Table 对象；空集合时 yield 空 Group。
        """
        items = self._renderables
        if not items:
            yield Group()
            return

        columns = min(self._max_columns, len(items))
        gap = max(0, self._column_gap)

        table = Table.grid(padding=0, expand=self._expand)
        for i in range(columns):
            table.add_column(ratio=1)
            if i < columns - 1:
                table.add_column(width=gap)

        row: list[RenderableType] = []
        for index, renderable in enumerate(items):
            if index and index % columns == 0:
                _pad_row(row, columns)
                table.add_row(*row)
                row = []
            row.append(renderable)
            if index % columns != columns - 1:
                row.append(Text(""))

        if row:
            _pad_row(row, columns)
            table.add_row(*row)

        yield table


def _pad_row(row: list[RenderableType], columns: int) -> None:
    """补齐行中的空单元格，使其包含 columns 个数据列和 (columns - 1) 个间隙列。"""
    expected = columns * 2 - 1
    while len(row) < expected:
        row.append(Text(""))
