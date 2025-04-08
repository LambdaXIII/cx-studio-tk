from collections.abc import Generator
from typing import Protocol, runtime_checkable

from rich.console import (
    RenderableType,
)
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from .rich_label import RichLabel, RichLabelMixin


@runtime_checkable
class RichDetailMixin(Protocol):
    def __rich_detail__(self) -> Generator: ...


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

        if hasattr(item, "__rich_repr__"):
            table = Table(box=None, show_header=False)
            table.add_column("key", justify="right", style="bold yellow")
            table.add_column("value", justify="left", overflow="fold")
            for tup in item.__rich_repr__():
                key, value = "", ""
                if isinstance(tup, tuple):
                    match len(tup):
                        case 0:
                            continue
                        case 1:
                            value = tup[0]
                        case 2:
                            key, value = tup
                        case _:
                            key, *values = tup
                            value = list(values)
                else:
                    value = tup
                table.add_row(key, RichDetailPanel._check_value(value))
            return table
        return item

    @staticmethod
    def _check_value(item):
        if isinstance(item, RichLabelMixin):
            return RichLabel(item)
        if isinstance(item, RichDetailMixin):
            return RichDetail(item)
        if isinstance(item, RenderableType):
            return item
        return Pretty(item)

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
