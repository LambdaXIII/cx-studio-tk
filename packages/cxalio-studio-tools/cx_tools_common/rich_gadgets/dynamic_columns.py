from collections.abc import Sequence, Iterable

from rich.columns import Columns
from rich.console import Console, ConsoleOptions


class DynamicColumns:
    def __init__(
        self, renderables: Sequence | Iterable, max_columns: int = 2, expand=True
    ):
        self._renderables = list(renderables)
        self._max_columns = max_columns
        self._expand = expand

    def __rich_console__(self, console: Console, options: ConsoleOptions):
        w = (
            None
            if len(self._renderables) < self._max_columns
            else int(console.width / self._max_columns) - 1
        )
        yield Columns(self._renderables, expand=self._expand, equal=True, width=w)
