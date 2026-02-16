import re
from collections.abc import Iterable
from pathlib import Path, PurePath

from .inspector_info import InspectorInfo
from .media_path_inspector import MediaPathInspector


class EDLInspector(MediaPathInspector):
    FILENAME_PATTERN = re.compile(r"CLIP NAME: (.+)")

    def _is_inspectable(self, info: InspectorInfo) -> bool:
        if info.path.suffix != ".edl":
            return False
        if not info.is_decodable():
            return False
        return True

    def _inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        with open(info.path, "r", encoding=info.encoding) as fp:
            for line in fp:
                match = self.FILENAME_PATTERN.search(line)
                if match:
                    yield Path(match.group(1))
