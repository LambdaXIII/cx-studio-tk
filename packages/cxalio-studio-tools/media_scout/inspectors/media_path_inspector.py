from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import io
from pathlib import Path, PurePath
import os
from collections.abc import Iterable
from typing import IO, Literal, Self, override, AnyStr
from cx_studio.core import FileSize
from cx_studio.utils import EncodingUtils
from cx_studio.utils import StreamUtils

from .inspector_info import InspectorInfo


class MediaPathInspector(ABC):
    @abstractmethod
    def _is_inspectable(self, info: InspectorInfo) -> bool:
        pass

    def is_inspectable(self, info: InspectorInfo) -> bool:
        if not info.path.exists():
            return False

        return self._is_inspectable(info)

    @abstractmethod
    def _inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        pass

    def inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        try:
            yield from self._inspect(info)
        except UnicodeDecodeError:
            pass
