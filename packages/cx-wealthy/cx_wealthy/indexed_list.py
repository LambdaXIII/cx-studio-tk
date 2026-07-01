"""索引列表面板。"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .label import RichLabel

__all__ = ["IndexedListPanel"]


def _render_item(item: Any) -> RenderableType:
    """将列表项渲染为可渲染对象。

    优先使用 __rich__ 协议；若对象实现了 __rich_label__，则通过 RichLabel
    组装为标签文本；否则退回到字符串表示。
    """
    if hasattr(item, "__rich__"):
        return item
    if hasattr(item, "__rich_label__"):
        return RichLabel(item).__rich__()
    return Text(str(item))


class IndexedListPanel:
    """索引列表面板：带行号索引的列表展示。

    修复旧版 IndexedListPanel 的索引错乱 bug。
    """

    def __init__(
        self,
        items: Iterable[Any],
        title: str | None = None,
        *,
        start_index: int = 1,
        max_lines: int | None = 20,
        border_style: str | None = None,
    ) -> None:
        """
        Args:
            items: 待展示的数据源
            title: 面板标题；None 时不显示
            start_index: 显示索引起始值，默认 1
            max_lines: 最大显示行数；None 表示不限
            border_style: 边框样式；None 时 "none"
        """
        self._items = list(items)
        self._title = title
        self._start_index = start_index
        self._max_lines = max_lines
        self._border_style = border_style

    def get_table(self) -> Table:
        """生成带索引的表格。

        索引修复：分离"显示索引"与"列表下标"。
        - 显示索引 = k + start_index（k 从 0 开始）
        - 列表下标 = k（0-based）
        """
        total = len(self._items)
        total_digits = len(str(total - 1 + self._start_index)) if total > 0 else 1
        table = Table(show_header=False, box=None)
        table.add_column(
            "#", justify="right", style="cyan", no_wrap=True, width=total_digits
        )
        table.add_column("Item")

        if total == 0:
            table.add_row("", "(empty)")
            return table

        def add_row(index: int | str, item: Any) -> None:
            index_str = (
                str(index).rjust(total_digits) if isinstance(index, int) else str(index)
            )
            table.add_row(index_str, _render_item(item))

        if self._max_lines is None or self._max_lines >= total:
            for k, item in enumerate(self._items):
                add_row(k + self._start_index, item)
        else:
            head = self._max_lines - 2
            for k in range(head):
                add_row(k + self._start_index, self._items[k])
            skipped = total - head - 1
            add_row("...", f"... skipped {skipped} items ...")
            add_row(total - 1 + self._start_index, self._items[-1])

        return table

    def __rich__(self) -> Panel:
        return Panel(
            self.get_table(),
            title=self._title,
            border_style=self._border_style or "none",
        )
