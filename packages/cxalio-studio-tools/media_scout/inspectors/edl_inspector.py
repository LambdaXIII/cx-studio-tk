from collections.abc import Iterable
from .inspector_info import InspectorInfo
from .media_path_inspector import MediaPathInspector
from pathlib import Path, PurePath
import re


class EDLInspector(MediaPathInspector):
    FILENAME_PATTERN = re.compile(r"CLIP NAME: (.+)")

    def _is_inspectable(self, info: InspectorInfo) -> bool:
        assert info.path.suffix == ".edl"
        assert info.is_decodable()
        return True

    def _inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        with open(info.path, "r", encoding=info.encoding) as fp:
            for line in fp:
                match = self.FILENAME_PATTERN.match(line)
                if match:
                    yield Path(match.group(1))
