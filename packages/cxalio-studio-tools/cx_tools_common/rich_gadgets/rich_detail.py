from collections.abc import Generator
import enum
from typing import Iterable, Mapping, Protocol, Sequence, runtime_checkable

from .indexed_list_panel import IndexedListPanel
from pygments import highlight
from rich.console import (
    RenderableType,
)
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from .rich_label import RichLabel, RichLabelMixin
from .common import RichPrettyMixin
from rich.columns import Columns
from rich.text import Text
from rich import box
from rich.style import StyleType


@runtime_checkable
class RichDetailMixin(Protocol):
    def __rich_detail__(self) -> Generator: ...


class RichDetail:
    def __init__(self, item: RichDetailMixin):
        self._item = item

    def __rich_repr__(self):
        yield from self._item.__rich_detail__()


class RichDetailTable:
    _SUB_BOX_BORDER_STYLE = "grey70"

    def __init__(
        self,
        item: RichDetailMixin | RichPrettyMixin | Mapping | dict,
        sub_box: bool = True,
    ) -> None:
        self._item = item
        self._sub_box = sub_box

    def make_table(self, item):
        table = Table(
            show_header=False,
            box=None,
        )
        table.add_column("key", justify="left", style="italic yellow", no_wrap=True)
        table.add_column("value", justify="left", overflow="fold", highlight=True)

        iterator = None
        if isinstance(item, RichDetailMixin):
            iterator = item.__rich_detail__()
        elif isinstance(item, RichPrettyMixin):
            iterator = item.__rich_repr__()
        elif isinstance(item, Mapping | dict):
            iterator = item.items()
        elif isinstance(item, Iterable):
            iterator = [None, list(item)]

        if iterator is None:
            return table

        for tup in iterator:
            if not isinstance(tup, tuple):
                continue
            key, value = None, None
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
            table.add_row(key, self.__check_value(value))

        return table

    def __check_value(
        self, value, disable_sub_box: bool = False
    ) -> RenderableType | None:
        if value is None:
            return None
        if isinstance(value, Mapping | dict | RichDetailMixin | RichPrettyMixin):
            if self._sub_box and not disable_sub_box:
                return RichDetailPanel(
                    value,
                    border_style=self._SUB_BOX_BORDER_STYLE,
                    sub_box=False,
                    title=value.__class__.__name__,
                )
            return self.make_table(value)
        if isinstance(value, RichLabelMixin):
            return RichLabel(value)
        if isinstance(value, RenderableType):
            return value
        if isinstance(value, Sequence | Iterable):
            list_panel = IndexedListPanel(
                list(self.__check_value(v, disable_sub_box=True) for v in value),
                title=value.__class__.__name__,
                border_style=self._SUB_BOX_BORDER_STYLE,
            )
            if self._sub_box and not disable_sub_box:
                return list_panel
            return list_panel.get_table()
        return Pretty(value)

    def __rich__(self):
        return self.make_table(self._item)


class RichDetailPanel:
    def __init__(
        self,
        item: RichDetailMixin | RichPrettyMixin | Mapping | dict,
        title: str | None = None,
        border_style: StyleType | None = None,
        sub_box: bool = True,
    ):
        self._item = item
        self._title = title
        self._border_style = border_style or "none"
        self._sub_box = sub_box

    def __rich__(self):
        content = RichDetailTable(self._item, sub_box=self._sub_box)

        panel = Panel(
            content,
            title=self._title,
            subtitle=self._item.__class__.__name__,
            title_align="left",
            subtitle_align="right",
            expand=True,
            border_style=self._border_style,
        )
        return panel
