from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import os
from collections.abc import AsyncIterable
from typing import IO, Literal, Self, override
from cx_studio.core import FileSize
from cx_studio.utils import EncodingUtils


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
    async def is_inspectable(self, sample: Sample) -> bool:
        pass

    @abstractmethod
    async def inspect(self, content: IO[bytes] | bytes) -> AsyncIterable[str]:
        pass
