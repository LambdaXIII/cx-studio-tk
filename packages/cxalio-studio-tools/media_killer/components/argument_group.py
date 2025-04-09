from dataclasses import dataclass, field
from pathlib import Path
import stat
from typing import Literal

from cx_studio.utils import FunctionalUtils
from collections.abc import Generator, Iterable
from collections import defaultdict
from rich.columns import Columns
import threading


class ArgumentGroup:
    def __init__(
        self,
        options: dict | str | list | None = None,
        filename: Path | None = None,
        **kwargs,
    ):
        self.filename: Path | None = filename
        self._options: dict[str, list[str]] = defaultdict(list)
        self._position_arguments: list[str] = []
        if options:
            self.add_options(options)
        self.add_options(**kwargs)

    @staticmethod
    def __iter_pairs_from_list(args: list) -> Generator[tuple[str | None, str | None]]:
        prev = None
        for x in args:
            x = str(x)
            if x.startswith("-"):
                # if prev:
                yield x, None
                prev = x
            else:
                yield prev, x
                prev = None

    def __add_options_from_pairs(self, pairs: Iterable[tuple[str | None, str | None]]):
        for k, v in pairs:
            # print(k, v)
            k = self._deformat_key(k)
            v = str(v) if v else None
            if k and v:
                self._options[k].append(v)
                continue

            if k and not v and k not in self._options:
                self._options[k] = []
                continue

            if not k and v:
                self._position_arguments.append(v)

    def __make_pairs(
        self, options: str | list | dict
    ) -> Iterable[tuple[str | None, str | None]]:
        pairs = []
        if isinstance(options, dict):
            pairs = options.items()
        elif isinstance(options, list):
            pairs = self.__iter_pairs_from_list(options)
        elif isinstance(options, str):
            pairs = self.__iter_pairs_from_list(options.split(" "))
        return pairs

    def add_options(
        self, options: str | list | dict | None = None, *args, **kwargs
    ) -> "ArgumentGroup":
        pair_iterators = []
        if options:
            pair_iterators.append(self.__make_pairs(options))

        if args:
            pair_iterators.append(self.__make_pairs(list(args)))

        if kwargs:
            pair_iterators.append(self.__make_pairs(kwargs))

        for pairs in pair_iterators:
            self.__add_options_from_pairs(pairs)
        return self

    @staticmethod
    def _format_key(key: str) -> str:
        return key if key.startswith("-") else f"-{key}"

    @staticmethod
    def _deformat_key(key: object | None) -> str | None:
        if key is None:
            return None
        key = str(key)
        result = key[1:] if key.startswith("-") else key
        return result if len(result) > 0 else None

    def items(self) -> Generator[tuple[str, list]]:
        for k, v in self._options.items():
            yield self._format_key(k), v

    def iter_arguments(
        self,
        position_for_position_arguments: Literal[
            "front", "back", "nowhere"
        ] = "nowhere",
    ) -> Generator[str]:
        if position_for_position_arguments == "front":
            yield from self._position_arguments

        for k, v in self._options.items():
            key = self._format_key(k)
            if not v:
                yield key
            else:
                for value in v:
                    yield key
                    yield value

        if position_for_position_arguments == "back":
            yield from self._position_arguments

    def __rich_repr__(self):
        if self._position_arguments:
            yield "位置参数", Columns(self._position_arguments)
        if self._options:
            for k, v in self.items():
                yield k, Columns(v)
        if self.filename:
            yield "文件名", self.filename
