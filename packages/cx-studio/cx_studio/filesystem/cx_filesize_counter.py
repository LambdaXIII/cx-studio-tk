"""文件大小计数器。

统计输入和输出文件的总大小，用于显示转码前后的文件大小对比。
"""

from collections.abc import Iterable
from cx_studio.core.cx_filesize import FileSize
from pathlib import Path


class FileSizeCounter:
    """文件大小计数器。

    累计记录的文件路径集合大小，提供 total_size 属性获取汇总。
    """

    def __init__(self) -> None:
        self._paths: set[Path] = set()

    def add_paths(self, paths: Iterable[Path]) -> None:
        """添加文件路径到计数集合。

        Args:
            paths: 文件路径迭代器
        """
        for p in paths:
            self._paths.add(Path(p))

    @property
    def total_size(self) -> "FileSizeCounter.TotalSize":
        return self.TotalSize(self._paths)

    class TotalSize:
        """文件大小汇总。"""

        def __init__(self, paths: set[Path]) -> None:
            self._paths = paths

        @property
        def total_bytes(self) -> int:
            """所有文件的总字节数。"""
            total = 0
            for p in self._paths:
                try:
                    total += p.stat().st_size
                except OSError:
                    pass
            return total

        def __str__(self) -> str:
            return FileSize.from_bytes(self.total_bytes).pretty_string

        def __rich__(self) -> str:
            return str(self)
