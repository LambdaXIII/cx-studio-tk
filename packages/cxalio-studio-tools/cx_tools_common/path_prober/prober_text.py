import re
from collections.abc import Generator
from io import TextIOBase
from pathlib import PurePath, Path
from urllib.parse import unquote

from cx_studio.utils import PathUtils
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

    def __init__(self, *acceptable_suffixes: str | None):
        self._acceptable_suffixes = set()
        for s in acceptable_suffixes:
            suffix = PathUtils.normalize_suffix(str(s))
            self._acceptable_suffixes.add(suffix) if suffix else None
        # 如果没有制定扩展名，则默认接受任何文件

    def pre_check(self, filename: str | Path) ->bool:
        return Path(filename).suffix.lower() in self._acceptable_suffixes if len(self._acceptable_suffixes) > 0 else True

    def _is_acceptable(self, fp: TextIOBase) -> bool:
        if len(self._acceptable_suffixes):
            return True
        suffix = self._get_suffix(fp)
        return suffix is None or suffix in self._acceptable_suffixes

    def _parse_url(self, line: str) -> str | None:
        line = unquote(line)
        match = self._URL_PATTERN.search(line)
        return match.group(1) if match else None

    def _parse_path(self, line: str) -> str | None:
        match = self._PATH_PATTERN.search(line)
        return match.group(0) if match else None

    def _probe(self, fp: TextIOBase) -> Generator[PurePath]:
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
