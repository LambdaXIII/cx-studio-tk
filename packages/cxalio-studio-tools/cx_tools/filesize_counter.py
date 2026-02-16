from collections.abc import Iterable
from pathlib import Path

from cx_studio.core import FileSize


class FileSizeCounter:
    def __init__(self, paths: Iterable[Path | str] | None = None) -> None:
        self._paths = [Path(x) for x in paths or []]

    def add_path(self, path: Path | str):
        self._paths.append(Path(path))

    def add_paths(self, paths: Iterable[Path | str]):
        self._paths.extend([Path(x) for x in paths])

    @property
    def total_size(self) -> FileSize:
        if not self._paths:
            return FileSize.from_bytes(0)
        sizes = sum([x.stat().st_size if x.exists() else 0 for x in self._paths])
        return FileSize.from_bytes(sizes)
