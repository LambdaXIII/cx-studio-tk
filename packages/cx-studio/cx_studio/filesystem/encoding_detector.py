import os
from functools import lru_cache
from pathlib import Path

from chardet import UniversalDetector
from lazy_object_proxy import Proxy

__CHARDET = Proxy(UniversalDetector)


@lru_cache(maxsize=128)
def detect_file_encoding(
    file_path: os.PathLike, default_encoding: str | None = "utf-8"
) -> str:
    filename = Path(file_path)
    __CHARDET.reset()
    try:
        with open(filename, "rb") as fp:
            max_len = 200 * 1024 * 20
            while not __CHARDET.done and max_len > 0:
                line = fp.read(200 * 1024)
                if line == b"":
                    break
                __CHARDET.feed(line)
                max_len -= len(line)
            result = __CHARDET.result
            return result["encoding"]
    except FileNotFoundError:
        return default_encoding or "locale"
