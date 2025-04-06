from abc import ABC
from collections.abc import Iterable
from typing import Literal

from rich.segment import Segment
from rich.text import Text
import rich.markup


class RichLabel:
    def __init__(
        self,
        obj: object,
        markup=True,
        sep: str = "\t",
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

    def __rich__(self):
        cls_name = self._obj.__class__.__name__
        func = self._get_func(self._obj)
        if func:
            text = Text(
                tab_size=self._tab_size, overflow=self._overflow, justify=self._justify
            )
            for s in func():
                if isinstance(s, Segment):
                    text.append_tokens([(s.text, s.style)])
                elif isinstance(s, str):
                    t = (
                        Text.from_markup(s)
                        if self._markup
                        else Text(rich.markup.escape(s))
                    )
                    text.append_text(t)
                else:
                    text.append_text(Text(str(s)))
                text.append_text(Text(self._sep))
            text.remove_suffix(self._sep)
            text.rstrip()
            return text
        return Text(f"[{cls_name}]")
