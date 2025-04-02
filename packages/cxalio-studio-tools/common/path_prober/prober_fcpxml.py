from io import TextIOBase
from pathlib import PurePath
from typing import Generator

from .path_prober import IPathProber
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote

class FcpXMLProber(IPathProber):
    _DOCTYPE_PATTERN = re.compile(r"<!DOCTYPE\s+fcpxml>")
    _URL_HEAD = re.compile(r"^file://.*/")
    def is_acceptable(self,fp:TextIOBase) ->bool:
        suffix = self._get_suffix(fp)
        if suffix is not None and suffix != ".fcpxml":
            return False

        with self.ProbeGuard(fp) as guard:
            guard.seek()
            for line in self._get_lines(fp):
                if self._DOCTYPE_PATTERN.search(line):
                    return True

    def probe(self,fp:TextIOBase) ->Generator[PurePath]:
        with self.ProbeGuard(fp) as guard:
            guard.seek()
            root = ET.parse(fp.read())
            for node in root.iter("media-rep"):
                kind = node.get("kind")
                if kind=="original-media":
                    url = unquote(node.get("src"))
                    if self._URL_HEAD.match(url):
                        p = self._URL_HEAD.sub("",url)
                        if guard.is_new(p):
                            yield PurePath(p)

