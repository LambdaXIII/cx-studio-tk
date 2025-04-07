from abc import ABC
from collections.abc import Iterable
from pyclbr import Function
from typing import Literal

from rich.segment import Segment
from rich.text import Text
import rich.markup
from cx_studio.utils import FunctionalUtils


class RichLabel:
    def __init__(
        self,
        obj: object,
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

    def _get_func(self, obj: object):
        cls_name = self._obj.__class__.__name__
        mangled_name = f"_{cls_name}__rich_label__"
        if hasattr(self._obj, mangled_name):
            return getattr(self._obj, mangled_name)
        func_name = "__rich_label__"
        if hasattr(self._obj, func_name):
            return getattr(self._obj, func_name)
        return None

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
        cls_name = self._obj.__class__.__name__
        func = self._get_func(self._obj)
        if func:
            text = Text.assemble(
                *[
                    self.__check_element(x)
                    for x in FunctionalUtils.iter_with_separator(func(), self._sep)
                ],
                tab_size=self._tab_size,
                overflow=self._overflow,
                justify=self._justify,
            )
            return text
        return Text(f"[{cls_name}]")
