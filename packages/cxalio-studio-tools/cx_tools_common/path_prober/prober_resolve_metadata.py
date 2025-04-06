import csv
from io import TextIOBase
from pathlib import PurePath, Path
from typing import Generator

from .path_prober import IPathProber


class ResolveMetadataCSVProber(IPathProber):
    @staticmethod
    def _get_headers(fp: TextIOBase) -> list[str]:
        with IPathProber.ProbeGuard(fp) as guard:
            guard.seek()
            for line in fp:
                if line.strip() != "":
                    return line.split(",")
        return []

    def pre_check(self, filename: str | Path) -> bool:
        return Path(filename).suffix.lower() == ".fcpxml"

    def _is_acceptable(self, fp: TextIOBase) -> bool:
        suffix = self._get_suffix(fp)
        if suffix is not None and suffix != ".csv":
            return False
        headers = self._get_headers(fp)
        return "File Name" in headers and "Clip Directory" in headers

    def _probe(self, fp: TextIOBase) -> Generator[PurePath]:
        headers = self._get_headers(fp)
        with IPathProber.ProbeGuard(fp) as guard:
            guard.seek()
            reader = csv.DictReader(fp, fieldnames=headers)
            for row in reader:
                name = row["File Name"]
                folder = row["Clip Directory"]
                if name == "File Name" or folder == "Clip Directory":
                    continue
                result = PurePath(folder, name)
                if guard.is_new(result):
                    yield result
