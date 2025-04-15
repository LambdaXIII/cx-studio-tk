from collections.abc import Generator
from typing import Literal
from typing import Protocol, runtime_checkable

from cx_studio.utils import FunctionalUtils
from . import rich_types as r


@runtime_checkable
class WealthLabelMixin(Protocol):
    def __rich_label__(self) -> Generator: ...


class WealthLabel:
    def __init__(
        self,
        obj: WealthLabelMixin,
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
        if isinstance(item, WealthLabelMixin):
            for x in item.__rich_label__():
                yield from self.__unpack_item(x)
        elif isinstance(item, WealthLabel):
            yield from self.__unpack_item(item._obj)
        elif isinstance(item, str):
            yield r.Text.from_markup(item) if self._markup else r.markup.escape(item)
        elif isinstance(item, r.Text):
            yield item
        elif isinstance(item, r.Segment):
            yield item.text
            if item.style:
                yield item.style
        else:
            yield str(item)

    def __rich__(self):
        if not isinstance(self._obj, WealthLabelMixin):
            cls_name = self._obj.__class__.__name__
            return r.Pretty(f"[{cls_name}] (instance)")

        elements = self.__unpack_item(self._obj)
        elements_with_sep = list(
            FunctionalUtils.iter_with_separator(elements, self._sep)
        )
        text = r.Text.assemble(
            *elements_with_sep,  # type:ignore
            tab_size=self._tab_size,
            overflow=self._overflow,
            justify=self._justify,
        )
        return text
