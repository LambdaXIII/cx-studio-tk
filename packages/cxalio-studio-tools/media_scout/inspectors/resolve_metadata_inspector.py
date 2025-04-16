from pathlib import PurePath
from .media_path_inspector import MediaPathInspector, Sample
from collections.abc import Iterable
from typing import IO, AnyStr
import csv


class ResolveMetadataInspector(MediaPathInspector):
    def __init__(self, sep: str | None = None):
        super().__init__()
        self.sep = sep or ","

    def _get_headers(self, fp: IO[bytes] | bytes, encoding: str = "utf-8") -> list[str]:
        for line in self.readlines(fp, encoding=encoding):
            line = line.strip()
            if self.sep in line:
                return line.split(self.sep)
        return []

    def _is_inspectable(self, sample: Sample) -> bool:
        if sample.path.suffix != ".csv":
            return False
        headers = self._get_headers(sample.content)
        return (
            len(headers) > 0 and "File Name" in headers and "Clip Directory" in headers
        )

    def _inspect(self, sample: Sample) -> Iterable[PurePath]:
        with open(sample.path, "rb") as fp:
            headers = self._get_headers(fp)
            reader = csv.DictReader(
                self.readlines(fp), fieldnames=headers, delimiter=self.sep
            )
            for row in reader:
                name = row.get("File Name")
                folder = row.get("Clip Directory")
                if name == "File Name" or folder == "Clip Directory":
                    continue
                if name and folder:
                    yield PurePath(folder, name)
