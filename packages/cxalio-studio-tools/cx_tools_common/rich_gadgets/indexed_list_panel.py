from typing import Iterable
from rich.table import Table
from rich.panel import Panel
from collections.abc import Sequence

from rich.console import Console
from collections.abc import Callable

class IndexedListPanel:
    def __init__(self,items: Sequence | Iterable, title: str | None = None, start_index=1, max_lines=20,width:int|Callable[[Console],int]=None):
        self._items = list(items)
        self._title = title
        self._start_index = start_index
        self._max_lines = max_lines
        self._width = width or self.default_width_calculator


    @staticmethod
    def default_width_calculator(console:Console)->int:
        return int(console.width * 0.8)

    def get_table(self)->Table:
        table = Table(box=None, show_header=False)
        table.add_column("index", justify="right", style="green", ratio=1)
        table.add_column("content", justify="left", style="yellow", overflow="fold", ratio=200)

        total = len(self._items)
        total_digits = len(str(total))

        for i, item in enumerate(self._items, start=self._start_index):
            if self._max_lines and i > self._max_lines:
                table.add_row(f"[red]{'-' * (total_digits + 2)}[/]", f"[italic red]skipped {total - i - 1} items...[/]")
                table.add_row(f"[{total}]", str(self._items[-1]))
                break
            table.add_row(f"[{i:>{total_digits}}]", str(item))

        return table

    def __rich_console__(self, console, _options):
        table=self.get_table()
        total = len(self._items)
        panel_width = self._width if isinstance(self._width,int) else self._width(console)
        yield Panel(table,title=self._title,title_align="left",
                    subtitle=f"{total} items",subtitle_align="right",
                    width=panel_width)

