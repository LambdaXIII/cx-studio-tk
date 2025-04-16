from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import os
from collections.abc import Iterable
from typing import IO, Literal, Self, override
from cx_studio.core import FileSize
from cx_studio.utils import EncodingUtils
from cx_studio.utils import StreamUtils


@dataclass
class Sample:
    path: Path
    size: FileSize
    encoding: str = "locale"
    content: bytes = field(default_factory=bytes)

    @classmethod
    def load(cls, filename: str | os.PathLike) -> Sample:
        path = Path(filename)
        size = FileSize(path.stat().st_size) if path.exists() else FileSize(0)
        encoding = EncodingUtils.detect_encoding(path)
        with open(path, "rb") as f:
            content = f.read(1024)
        return cls(path, size, encoding, content)


class MediaPathInspector(ABC):
    @abstractmethod
    def _is_inspectable(self, sample: Sample) -> bool:
        pass

    def is_inspectable(self, sample: Sample) -> bool:
        if not sample.path.exists():
            return False
        return self._is_inspectable(sample)

    @abstractmethod
    def _inspect(self, content: IO[bytes] | bytes) -> Iterable[str]:
        pass

    def inspect(self, sample: Sample) -> Iterable[str]:
        if not self.is_inspectable(sample):
            return
        with open(sample.path, "rb") as f:
            yield from self._inspect(f)

    @staticmethod
    def readlines(
        fp: IO[bytes] | bytes,
        *,
        max_lines: int | None = None,
        skip_empty: bool = True,
        encoding: str | None = None,
    ) -> Iterable[str]:
        stream = StreamUtils.wrap_io(fp)
        line_count = 0
        for line in StreamUtils.readlines_from_stream(stream):
            if skip_empty and not line.strip():
                continue
            yield line.decode(encoding or "utf-8")
            line_count += 1
            if max_lines and line_count >= max_lines:
                break
