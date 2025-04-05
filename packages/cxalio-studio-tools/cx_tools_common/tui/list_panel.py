from typing import Iterable
from rich.table import Table
from rich.panel import Panel
from collections.abc import Sequence


def indexed_list_panel(
    items: Sequence | Iterable, title: str | None = None, start_index=1
) -> Panel:
    table = Table(box=None, show_header=False)
    table.add_column("index", justify="right", style="green")
    table.add_column("content", justify="left", style="yellow", overflow="fold")
    for i, item in enumerate(items, start_index):
        table.add_row(f"[{i}]", str(item))
    return Panel(table, title=title, title_align="left")
