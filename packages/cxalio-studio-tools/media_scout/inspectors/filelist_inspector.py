import re
import urllib.parse
from collections.abc import Iterable
from pathlib import PurePath

from .inspector_info import InspectorInfo
from .media_path_inspector import MediaPathInspector


class FileListInspector(MediaPathInspector):
    PATH_PATTERN = re.compile(
        r"""
        ^                           # 路径开始
        (?:                         # 非捕获组，匹配 Windows 驱动器或 Unix 根目录
            [A-Za-z]:\\?            # Windows 驱动器（可选反斜杠）
            |
            /                       # Unix/Linux/Mac 根目录
        )?
        (?:                         # 非捕获组，匹配路径中的目录和文件名
            [^\\/:*?"<>|\r\n]+      # 匹配除特殊字符外的任意字符
            (?:\\|/)                # 目录分隔符
        )*
        [^\\/:*?"<>|\r\n]*          # 最后的目录或文件名
        $                           # 路径结束
        """,
        re.VERBOSE,
    )

    URL_PATTERN = re.compile(r"file://.*/(\S+)")

    def __init__(self, *extensions: str):
        super().__init__()
        self.acceptable_extensions = set(extensions)

    def _is_inspectable(self, info: InspectorInfo) -> bool:
        if self.acceptable_extensions:
            if not info.path.suffix in self.acceptable_extensions:
                return False

        if not info.is_decodable():
            return False
        return True

    def _parse_url(self, line: str) -> str | None:
        match = self.URL_PATTERN.search(urllib.parse.unquote(line))
        return match.group(1) if match else None

    def _parse_path(self, line: str) -> str | None:
        match = self.PATH_PATTERN.search(line)
        return match.group(0) if match else None

    def _inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        with open(info.path, "r", encoding=info.encoding) as fp:
            for line in fp:
                if (url := self._parse_url(line)) is not None:
                    yield PurePath(url)
                    continue
                if (path := self._parse_path(line)) is not None:
                    yield PurePath(path)
                    continue
