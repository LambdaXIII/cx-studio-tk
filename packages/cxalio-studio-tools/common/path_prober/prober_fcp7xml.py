import re
from collections.abc import Generator
from io import TextIOBase

from .path_prober import IPathProber

from pathlib import PurePath
import xml.etree.ElementTree as ET
from urllib.parse import unquote


class Fcp7XMLProber(IPathProber):
    _DOCTYPE_PATTERN = re.compile(r"<!DOCTYPE\s+xmeml>")
    _URL_HEAD = re.compile(r"^file://.*/")
    def is_acceptable(self,fp:TextIOBase) ->bool:
        suffix = self._get_suffix(fp)
        if suffix is not None and suffix != ".xml":
            return False
        cursor = fp.tell()
        count = 0
        for line in fp:
            if self._DOCTYPE_PATTERN.search(line):
                return True
            count += 1
            if count > 10:
                break
        fp.seek(cursor)
        return False

    def probe(self,fp:TextIOBase) ->Generator[PurePath]:
        cursor = fp.tell()
        fp.seek(0)
        root = ET.fromstring(fp.read())
        fp.seek(cursor)
        for node in root.iter("pathurl"):
            url = unquote(node.text)
            if self._URL_HEAD.match(url):
                path = self._URL_HEAD.sub("",url)
                if len(path) > 0:
                    yield PurePath(path)

