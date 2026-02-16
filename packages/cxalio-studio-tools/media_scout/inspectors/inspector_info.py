import io
import os
from collections import namedtuple
from collections.abc import Iterable
from pathlib import Path

from cachetools import LRUCache
from chardet import UniversalDetector

from cx_studio.core import FileSize


class InspectorInfo:
    _sample_cache = LRUCache(maxsize=128)
    _Record = namedtuple("_Record", ["encoding", "sample"])

    def __init__(self, path: os.PathLike, sample_size_hint: int = 2048):
        self.path = Path(path)
        self.size = FileSize(os.path.getsize(path))
        self.encoding: str = "locale"
        self.sample: bytes = b""

        if not self.path.is_file():
            return

        _record: InspectorInfo._Record | None = self._sample_cache.get(path)

        if (
            _record is None
            or len(_record.sample) < sample_size_hint < self.size.total_bytes
        ):
            detector = UniversalDetector()
            detector.reset()
            _sample = bytearray()
            with open(path, "rb") as f:
                while not (detector.done or len(_sample) >= sample_size_hint):
                    raw = f.read(io.DEFAULT_BUFFER_SIZE)
                    if not raw:
                        break
                    detector.feed(raw)
                    _sample.extend(raw)
                if len(_sample) < sample_size_hint:
                    extra = f.read(sample_size_hint - len(_sample))
                    _sample.extend(extra)
                    detector.feed(extra)
                detector.close()
                _encoding = detector.result["encoding"] or "locale"
            _record = InspectorInfo._Record(_encoding, bytes(_sample))
            self._sample_cache[path] = _record

        self.encoding, self.sample = _record.encoding, _record.sample

    def read_lines(
        self, lines: int = -1, ignore_empty_lines: bool = True
    ) -> Iterable[str]:
        with open(self.path, "r", encoding=self.encoding) as fp:
            n = 0
            for line in fp:
                if ignore_empty_lines and not line.strip():
                    continue
                yield line
                n += 1
                if 0 > n >= lines:
                    break

    def peek_first_line(self) -> str:
        for x in self.sample.splitlines(keepends=False):
            if x.strip():
                return x.decode(self.encoding)
        return ""

    def peek_lines(self, ignore_empty_lines: bool = True) -> Iterable[str]:
        for x in self.sample.splitlines(keepends=False):
            if ignore_empty_lines and not x.strip():
                continue
            if x.strip():
                yield x.decode(self.encoding)

    def is_decodable(self) -> bool:
        try:
            self.sample.decode(self.encoding)
            return True
        except UnicodeDecodeError:
            return False
