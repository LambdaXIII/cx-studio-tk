from io import TextIOBase
from typing import Generator

from .path_prober import IPathProber
from pathlib import Path,PurePath
import re

class EDLProber(IPathProber):
    FILENAME_PATTERN = r"CLIP NAME: (.+)"

    def is_acceptable(self,fp:TextIOBase) ->bool:
        suffix = self._get_suffix(fp)
        if suffix is not None and suffix != ".edl":
            return False
        return True

    def probe(self,fp:TextIOBase) ->Generator[PurePath]:
        cursor = fp.tell()
        fp.seek(0)
        for line in fp:
            match = re.search(self.FILENAME_PATTERN,line)
            if match is not None:
                yield PurePath(match.group(1))
        fp.seek(cursor)
