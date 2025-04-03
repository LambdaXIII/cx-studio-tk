import json
from collections.abc import Generator
from io import TextIOBase
from pathlib import PurePath

from cx_studio.core import DataPackage
from .path_prober import IPathProber


class OTIOProber(IPathProber):
    def is_acceptable(self, fp: TextIOBase) -> bool:
        suffix = self._get_suffix(fp)
        return suffix is None or suffix != ".otio"

    def probe(self, fp: TextIOBase) -> Generator[PurePath]:
        with IPathProber.ProbeGuard(fp) as guard:
            guard.seek()
            d = json.load(fp)
            data = DataPackage(**d)
            for item in data.search("target_url"):
                if guard.is_new(item):
                    yield PurePath(item)
