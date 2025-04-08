from abc import ABC
from collections.abc import Generator, Iterable
from pyclbr import Function
from typing import Literal

from rich.segment import Segment
from rich.text import Text
import rich.markup
from cx_studio.utils import FunctionalUtils
from typing import Protocol, runtime_checkable
from rich.console import RenderableType
from rich.pretty import Pretty


@runtime_checkable
class RichLabelMixin(Protocol):
    def __rich_label__(self) -> Generator: ...


class RichLabel:
    def __init__(
        self,
        obj: RichLabelMixin,
        markup=True,
        sep: str = " ",
        tab_size: int = 1,
        overflow: Literal["ignore", "crop", "ellipsis", "fold"] = "crop",
        justify: Literal["left", "center", "right"] = "left",
    ):
        self._obj = obj
        self._markup = markup
        self._tab_size = tab_size
        self._sep = sep
        self._overflow: Literal["ignore", "crop", "ellipsis", "fold"] = overflow
        self._justify: Literal["left", "center", "right"] = justify

    def __unpack_item(self, item):
        if isinstance(item, RichLabelMixin):
            for x in item.__rich_label__():
                yield from self.__unpack_item(x)
        elif isinstance(item, RichLabel):
            yield from self.__unpack_item(item._obj)
        elif isinstance(item, str):
            yield Text.from_markup(item) if self._markup else rich.markup.escape(item)
        elif isinstance(item, Text):
            yield item
        elif isinstance(item, Segment):
            yield item.text
            if item.style:
                yield item.style
        else:
            yield str(item)

    def __rich__(self):
        if not isinstance(self._obj, RichLabelMixin):
            cls_name = self._obj.__class__.__name__
            return Pretty(f"[{cls_name}] (instance)")

        elements = self.__unpack_item(self._obj)
        elements_with_sep = list(
            FunctionalUtils.iter_with_separator(elements, self._sep)
        )
        text = Text.assemble(
            *elements_with_sep,
            tab_size=self._tab_size,
            overflow=self._overflow,
            justify=self._justify,
        )
        return text
