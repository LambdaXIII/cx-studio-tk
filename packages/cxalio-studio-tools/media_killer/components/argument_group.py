from dataclasses import dataclass, field
from pathlib import Path

from cx_studio.utils import FunctionalUtils
from rich.columns import Columns


@dataclass()
class ArgumentGroup:
    filename: Path | None = None
    options: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def _format_key(key: str):
        return key if key.startswith("-") else f"-{key}"

    @staticmethod
    def _iter_sequence(*args):
        for arg in FunctionalUtils.flatten_list(*args):
            a = str(arg)
            if " " in a:
                yield from a.split(" ")
            else:
                yield a

    def _set_option(self, k, v):
        key = k[1:] if k.startswith("-") else k
        self.options[key] = v

    def add_options(self, *args, **kwargs):
        prev_key = None
        for a in self._iter_sequence(*args):
            if a.startswith("-"):
                if prev_key is not None:
                    self._set_option(prev_key, None)
                prev_key = a
            else:
                if prev_key is not None:
                    self._set_option(prev_key, a)
                    prev_key = None
        if prev_key is not None:
            self._set_option(prev_key, None)

        for k, v in kwargs.items():
            self._set_option(k, v)

    def iter_arguments(self):
        for k, v in self.options.items():
            yield self._format_key(k)
            if v is not None:
                yield str(v)

    def __rich_repr__(self):
        if self.filename is not None:
            yield "filename", self.filename
        yield " ".join(x for x in self.iter_arguments())
