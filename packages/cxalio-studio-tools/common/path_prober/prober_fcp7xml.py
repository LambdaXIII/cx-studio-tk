import re
import xml.etree.ElementTree as ET
from collections.abc import Generator
from io import TextIOBase
from pathlib import PurePath
from urllib.parse import unquote

from .path_prober import IPathProber


class Fcp7XMLProber(IPathProber):
    _DOCTYPE_PATTERN = re.compile(r"<!DOCTYPE\s+xmeml>")
    _URL_HEAD = re.compile(r"^file://.*/")

    def is_acceptable(self, fp: TextIOBase) -> bool:
        suffix = self._get_suffix(fp)
        if suffix is not None and suffix != ".xml":
            return False

        with self.ProbeGuard(fp) as guard:
            guard.seek()
            for line in self._get_lines(fp, 10):
                if self._DOCTYPE_PATTERN.search(line):
                    return True

    def probe(self, fp: TextIOBase) -> Generator[PurePath]:
        with self.ProbeGuard(fp) as guard:
            guard.seek()
            root = ET.fromstring(fp.read())

            for node in root.iter("pathurl"):
                url = unquote(node.text)
                if self._URL_HEAD.match(url):
                    path = self._URL_HEAD.sub("", url)
                    if guard.is_new(path) and len(path) > 0:
                        yield PurePath(path)
