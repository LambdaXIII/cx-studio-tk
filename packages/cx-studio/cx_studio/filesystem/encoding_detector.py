"""文件字符编码探测工具。

基于 chardet 的 UniversalDetector 读取文件内容片段进行编码判定，
结果按路径通过 lru_cache 缓存；文件不存在时回退到默认编码。
"""

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
    """探测文件的字符编码，结果按路径缓存。

    最多读取约 4 MiB 内容（每轮 200 KiB，至多 20 轮）喂给 chardet 的
    UniversalDetector，检测器给出明确结论或文件读完即止；探测完成后
    关闭检测器并返回其判定结果。仅当文件不存在（FileNotFoundError）
    时回退到 default_encoding，其余读取失败会原样向上抛出。
    结果由 lru_cache 按 file_path 缓存，重复探测同一文件不会重新读盘。

    Args:
        file_path: 待探测的文件路径。
        default_encoding: 文件不存在时返回的回退编码；传 None 时
            回退为 "locale"。

    Returns:
        探测得到的编码名；文件不存在时返回回退编码。注意：对无法
        判定的内容（如空文件），chardet 可能返回 None。

    Raises:
        OSError: 文件存在但读取失败时（如权限不足、路径指向目录），
            由 open()/读取过程直接抛出。
    """
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
            __CHARDET.close()
            result = __CHARDET.result
            return result["encoding"]
    except FileNotFoundError:
        return default_encoding or "locale"
