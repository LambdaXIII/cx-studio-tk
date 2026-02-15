from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path, PurePath
from collections.abc import Iterable

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
