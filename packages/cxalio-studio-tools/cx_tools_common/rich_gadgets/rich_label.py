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
    def __rich_label__(self) -> Iterable | Generator: ...


class RichLabel:
    def __init__(
        self,
        obj: RichLabelMixin | RenderableType | object,
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

    def __check_element(self, element):
        if isinstance(element, str):
            return (
                Text.from_markup(element)
                if self._markup
                else rich.markup.escape(element)
            )
        if isinstance(element, Text):
            return element
        if isinstance(element, Segment):
            return (element.text, element.style) if element.style else element.text
        return str(element)

    def __rich__(self):
        if isinstance(self._obj, RichLabel):
            return self._obj

        if isinstance(self._obj, RichLabelMixin):
            text = Text.assemble(
                *[
                    self.__check_element(x)
                    for x in FunctionalUtils.iter_with_separator(
                        self._obj.__rich_label__(), self._sep
                    )
                ],
                tab_size=self._tab_size,
                overflow=self._overflow,
                justify=self._justify,
            )
            return text

        if isinstance(self._obj, RenderableType):
            return self._obj

        cls_name = self._obj.__class__.__name__
        return Pretty(f"[{cls_name}] (instance)")
