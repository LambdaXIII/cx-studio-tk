from collections.abc import Callable
from collections.abc import Sequence
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import rich.protocol
from rich.text import Text


class IndexedListPanel:
    def __init__(
        self,
        items: Sequence | Iterable,
        title: str | None = None,
        start_index=1,
        max_lines=20,
        width: int | Callable[[Console], int] | None = None,
    ):
        self._items = list(items)
        self._title = title
        self._start_index = start_index
        self._max_lines = max_lines
        # self._width = width or self.default_width_calculator
        self._width = width

    @staticmethod
    def default_width_calculator(console: Console) -> int:
        return int(console.width * 0.8)

    @staticmethod
    def __check_item(item):
        if rich.protocol.is_renderable(item):
            return item
        return str(item)

    def get_table(self) -> Table:
        table = Table(box=None, show_header=False)
        table.add_column("index", justify="right", style="green", ratio=1)
        table.add_column(
            "content", justify="left", style="yellow", overflow="fold", ratio=200
        )

        total = len(self._items)
        total_digits = len(str(total))

        for i, item in enumerate(self._items, start=self._start_index):
            if self._max_lines and i > self._max_lines:
                table.add_row(
                    f"[red][{'.' * total_digits}][/]",
                    f"[italic red]skipped {total - i - 1} items...[/]",
                )
                table.add_row(f"[{total}]", self.__check_item(self._items[-1]))
                break
            table.add_row(f"[{i:>{total_digits}}]", self.__check_item(item))

        return table

    def __rich__(self):
        content = (
            self.get_table() if len(self._items) > 0 else Text("(empty)", style="dim")
        )
        total = len(self._items)
        return Panel(
            content,
            title=self._title,
            title_align="left",
            subtitle=f"{total} items",
            subtitle_align="right",
        )
