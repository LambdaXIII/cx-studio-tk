import re
import urllib.parse
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import PurePath, Path

from .media_path_inspector import MediaPathInspector, InspectorInfo


class FCPXMLInspector(MediaPathInspector):
    DOCTYPE_PATTERN = re.compile(r"<!DOCTYPE\s+fcpxml>")
    URL_HEAD = re.compile(r"^file://.*?/")

    def _is_inspectable(self, info: InspectorInfo) -> bool:
        if info.path.suffix != ".fcpxml":
            return False
        if not info.is_decodable():
            return False
        for x in info.peek_lines():
            if self.DOCTYPE_PATTERN.search(x):
                return True
        return False

    def _inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        tree = ET.parse(info.path)
        root = tree.getroot()
        for node in root.iter("media-rep"):
            kind = node.get("kind")
            if kind == "original-media":
                url = urllib.parse.unquote(node.get("src") or "")
                if self.URL_HEAD.match(url):
                    yield PurePath(self.URL_HEAD.sub("", url))


class FCPXMLDInspector(MediaPathInspector):
    def __init__(self) -> None:
        super().__init__()
        self._inspector = FCPXMLInspector()

    def _is_inspectable(self, info: InspectorInfo) -> bool:
        if info.path.suffix != ".fcpxmld":
            return False
        if not info.path.is_dir():
            return False
        core_file = Path(info.path, "Info.fcpxml")
        core_info = InspectorInfo(core_file)
        return self._inspector.is_inspectable(core_info)

    def _inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        core_file = Path(info.path, "Info.fcpxml")
        core_info = InspectorInfo(core_file)
        yield from self._inspector.inspect(core_info)
