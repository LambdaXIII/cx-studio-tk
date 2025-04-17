from importlib.abc import InspectLoader
from pathlib import PurePath
from .media_path_inspector import MediaPathInspector
from collections.abc import Iterable
from typing import IO, AnyStr
import csv

from .inspector_info import InspectorInfo


class ResolveMetadataInspector(MediaPathInspector):
    DELIMITER = ","
    FILE_NAME_FIELD = "File Name"
    CLIP_DIRECTORY_FIELD = "Clip Directory"

    def _get_headers(self, info: InspectorInfo) -> list[str]:
        headers = info.peek_first_line().split(self.DELIMITER)
        return headers

    def _is_inspectable(self, info: InspectorInfo) -> bool:
        if info.path.suffix != ".csv":
            return False
        if not info.is_decodable():
            return False
        headers = self._get_headers(info)
        return (
            len(headers) > 0
            and self.FILE_NAME_FIELD in headers
            and self.CLIP_DIRECTORY_FIELD in headers
        )

    def _inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        headers = self._get_headers(info)
        with open(info.path, "r", encoding=info.encoding) as fp:
            reader = csv.DictReader(fp, fieldnames=headers, delimiter=self.DELIMITER)
            for row in reader:
                name = row.get(self.FILE_NAME_FIELD)
                folder = row.get(self.CLIP_DIRECTORY_FIELD)
                if name == self.FILE_NAME_FIELD or folder == self.CLIP_DIRECTORY_FIELD:
                    continue
                if name and folder:
                    yield PurePath(folder, name)
