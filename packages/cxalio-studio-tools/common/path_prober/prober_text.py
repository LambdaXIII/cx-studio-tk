import re
from collections.abc import Generator
from io import TextIOBase
from pathlib import PurePath
from urllib.parse import unquote

from .path_prober import IPathProber


class TextProber(IPathProber):
    _PATH_PATTERN = re.compile(
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
        re.VERBOSE
    )

    _URL_PATTERN = re.compile(r"file://.*/(\S+)")

    def is_acceptable(self, fp: TextIOBase) -> bool:
        return True

    def _parse_url(self, line: str) -> str | None:
        line = unquote(line)
        match = self._URL_PATTERN.search(line)
        return match.group(1) if match else None

    def _parse_path(self, line: str) -> str | None:
        match = self._PATH_PATTERN.search(line)
        return match.group(0) if match else None

    def probe(self, fp: TextIOBase) -> Generator[PurePath]:
        with IPathProber.ProbeGuard(fp) as guard:
            guard.seek()
            for line in fp:
                # line = TextUtils.auto_unquote(line)
                url = self._parse_url(line)
                if url is not None and guard.is_new(url):
                    yield PurePath(url)
                path = self._parse_path(line)
                if path is not None and guard.is_new(path):
                    yield PurePath(path)
