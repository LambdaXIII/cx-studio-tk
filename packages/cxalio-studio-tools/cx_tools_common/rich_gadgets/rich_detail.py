from collections.abc import Generator
from inspect import isclass
from re import sub
from typing import Any, Iterable, Protocol, runtime_checkable
from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    RichCast,
    RenderableType,
)
from rich.panel import Panel
from rich.table import Table
from rich.pretty import Pretty

from .rich_label import RichLabel, RichLabelMixin


@runtime_checkable
class RichDetailMixin(Protocol):
    def __rich_detail__(self) -> Generator | Iterable: ...


class RichDetail:
    def __init__(self, item: RichDetailMixin):
        self._item = item

    def __rich_repr__(self):
        yield from self._item.__rich_detail__()


class RichDetailPanel:
    def __init__(self, item: object, title: str | None = None):
        self._item = item
        self._title = title

    @staticmethod
    def _make_content(item):
        if isinstance(item, RichDetailMixin):
            item = RichDetail(item)

        if hasattr(item, "__rich_repr__") and not isclass(item):
            table = Table(box=None, show_header=False)
            table.add_column("key", justify="right", style="bold yellow")
            table.add_column("value", justify="left", overflow="fold")
            for tup in getattr(item, "__rich_repr__")():
                if not isinstance(tup, tuple) or not len(tup) >= 2:
                    continue
                key, value, *_ = tup
                v = RichLabel(value) if isinstance(value, RichLabelMixin) else value
                table.add_row(key, RichDetailPanel._make_content(v))
            return table

        if isinstance(item, RenderableType):
            return item

        return Pretty(item)

    # TODO: needs improvement

    def __rich__(self):
        content = self._make_content(self._item)
        panel = Panel(
            content,
            title=self._title,
            subtitle=self._item.__class__.__name__,
            title_align="left",
            subtitle_align="right",
            expand=True,
        )
        return panel
