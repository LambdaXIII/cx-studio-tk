from pathlib import PurePath
import re
from typing import Iterable
import xml.etree.ElementTree as ET


from .media_path_inspector import MediaPathInspector
from .inspector_info import InspectorInfo

import urllib.parse


class LegacyXMLInspector(MediaPathInspector):
    DOCTYPE_PATTERN = re.compile(r"<!DOCTYPE\s+xmeml>")
    URL_HEAD = re.compile(r"^file://.*?/")

    def _is_inspectable(self, info: InspectorInfo) -> bool:
        if info.path.suffix != ".xml":
            return False
        if not info.is_decodable():
            return False
        for line in info.peek_lines():
            if self.DOCTYPE_PATTERN.search(line):
                return True
        return False

    def _inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        tree = ET.parse(info.path)
        root = tree.getroot()
        for node in root.iter("pathurl"):
            url = urllib.parse.unquote(node.text or "")
            if self.URL_HEAD.match(url):
                path = self.URL_HEAD.sub("", url)
                yield PurePath(path)
