import re
from io import TextIOBase
from pathlib import PurePath
from typing import Generator

from .path_prober import IPathProber


class EDLProber(IPathProber):
    FILENAME_PATTERN = r"CLIP NAME: (.+)"

    def is_acceptable(self, fp: TextIOBase) -> bool:
        suffix = self._get_suffix(fp)
        if suffix is not None and suffix != ".edl":
            return False
        return True

    def probe(self, fp: TextIOBase) -> Generator[PurePath]:
        with self.ProbeGuard(fp) as guard:
            for line in fp:
                match = re.search(self.FILENAME_PATTERN, line)
                if match is not None:
                    p = PurePath(match.group(1))
                    if guard.is_new(p):
                        yield PurePath(p)
