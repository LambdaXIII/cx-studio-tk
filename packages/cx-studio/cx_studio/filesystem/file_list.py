"""线程安全、自动去重的文件路径列表，按录入顺序追踪文件并延迟计算大小。

FileList 以规范化后的绝对路径字符串为键维护文件集合：追加时自动去重，
大小仅在访问 total_bytes 时通过 FileSizer 惰性获取并缓存，支持线程安全
的追加（append/push）、取出（take/pop）、迭代与总大小统计。
"""

from collections.abc import Callable, Iterator
from pathlib import Path
import threading

from cx_studio.core.file_size import FileSize

from . import PathUtils
from .file_sizer import FileSizer


class FileList:
    """线程安全的文件列表，按录入顺序追踪文件并自动去重。

    核心特性：
        - 顺序保证：文件按追加顺序存储，迭代时保持录入顺序
        - 自动去重：同一文件路径（规范化后）只保留一份
        - 延迟计算：文件大小仅在需要时通过 stat() 获取，避免不必要的系统调用
        - 线程安全：所有操作通过 threading.Lock 保护

    设计原则：
        - API 极简：仅提供追加(append/push)和取出(take/pop)操作
        - 去重基于路径：忽略文件大小变化，同一路径始终视为同一文件
        - 复杂操作交给消费方：如需排序、过滤等，提取为普通列表处理

    示例：
        >>> from cx_studio.filesystem.file_list import FileList
        >>> fl = FileList()
        >>> fl.append(Path("file1.txt"))
        True
        >>> fl.append(Path("file1.txt"))  # 重复路径被去重
        False
        >>> len(fl)
        1
        >>> fl.take()
        WindowsPath('C:/.../file1.txt')

    Args:
        sizer_function: 自定义文件大小计算函数。None 时使用默认实现。
            推荐注入带缓存的函数（如 functools.lru_cache）以提升性能。
    """

    def __init__(
        self,
        sizer_function: Callable[[Path], int] | None = None,
    ) -> None:
        self._file_sizer: FileSizer = FileSizer(sizer_function)
        self._lock: threading.Lock = threading.Lock()
        self._paths: list[str] = []
        self._bytes: dict[str, int | None] = {}

    def _get_bytes(self, key: str) -> int:
        """获取文件大小（字节），使用双重检查锁定实现延迟计算。

        首次调用时通过 FileSizer 获取大小并缓存，后续调用直接返回缓存值。

        Args:
            key: 规范化后的路径字符串。

        Returns:
            文件字节大小。
        """
        v = self._bytes[key]
        if v is None:
            with self._lock:
                v = self._bytes[key]
                if v is None:
                    v = self._file_sizer.get_bytes(Path(key))
                    self._bytes[key] = v
        return v

    @staticmethod
    def _make_key(path: Path | str) -> str:
        """将路径转换为规范化的字符串键。

        使用 path_utils.normalize_path 处理，确保不同格式的同一
        路径生成相同的键（如大小写、斜杠方向差异）。

        Args:
            path: 文件路径。

        Returns:
            规范化后的路径字符串。
        """
        return str(PathUtils.normalize_path(path))

    def append(self, path: Path) -> bool:
        """追加文件路径到列表末尾。

        自动去重：如果路径（规范化后）已存在，则不追加并返回 False。
        文件大小延迟计算，此时仅记录路径。

        Args:
            path: 要追加的文件路径。

        Returns:
            True：成功追加；False：路径已存在，未追加。
        """
        key = self._make_key(path)
        with self._lock:
            if key in self._bytes:
                return False
            self._paths.append(key)
            self._bytes[key] = None
            return True

    def push(self, path: Path) -> bool:
        """append 的别名，语义为"推入"。

        Args:
            path: 要推入的文件路径。

        Returns:
            True：成功推入；False：路径已存在，未推入。
        """
        return self.append(path)

    def take(self, index: int = 0) -> Path | None:
        """按索引取出文件路径并从列表中删除。

        默认取出第一个元素（FIFO 语义）。取出后相关的大小缓存也会被清除。

        Args:
            index: 要取出的元素索引，默认 0（第一个）。

        Returns:
            取出的文件路径；索引越界时返回 None。
        """
        with self._lock:
            if not 0 <= index < len(self._paths):
                return None
            key = self._paths[index]
            del self._bytes[key]
            del self._paths[index]
            return Path(key)

    def pop(self, index: int = 0) -> Path | None:
        """take 的别名，符合 Python 列表的传统命名习惯。

        Args:
            index: 要弹出的元素索引，默认 0（第一个）。

        Returns:
            弹出的文件路径；索引越界时返回 None。
        """
        return self.take(index)

    def __len__(self) -> int:
        """获取列表中的文件数量。

        Returns:
            当前列表中的文件数量。
        """
        with self._lock:
            return len(self._paths)

    def __iter__(self) -> Iterator[Path]:
        """返回同步迭代器，按录入顺序遍历文件路径。

        迭代时会创建快照，后续的追加/取出操作不影响当前迭代。

        Yields:
            文件路径（按录入顺序）。
        """
        with self._lock:
            snapshot = self._paths.copy()
        for key in snapshot:
            yield Path(key)

    class AsyncIterator:
        """异步迭代器，按录入顺序遍历文件路径。

        基于快照实现，迭代过程中不受列表变更影响。

        Args:
            file_list: 路径字符串列表快照。
        """

        def __init__(self, file_list: list[str]):
            self._data: list[str] = file_list
            self._index: int = 0

        def __aiter__(self) -> "FileList.AsyncIterator":
            """返回迭代器自身。"""
            return self

        async def __anext__(self) -> Path:
            """返回下一个文件路径。

            Returns:
                文件路径。

            Raises:
                StopAsyncIteration: 迭代完成时抛出。
            """
            if self._index >= len(self._data):
                raise StopAsyncIteration
            path = self._data[self._index]
            self._index += 1
            return Path(path)

    def __aiter__(self) -> "FileList.AsyncIterator":
        """返回异步迭代器，按录入顺序遍历文件路径。

        迭代时会创建快照，后续的追加/取出操作不影响当前迭代。

        Returns:
            AsyncIterator 实例。
        """
        with self._lock:
            snapshot = self._paths.copy()
        return FileList.AsyncIterator(snapshot)

    def __contains__(self, path: Path | str) -> bool:
        """判断文件路径是否已存在于列表中。

        路径会经过规范化处理后进行比较。

        Args:
            path: 要检查的文件路径。

        Returns:
            True：路径已存在；False：路径不存在。
        """
        key = self._make_key(path)
        with self._lock:
            return key in self._bytes

    @property
    def total_bytes(self) -> int:
        """计算所有文件的总字节数。

        触发延迟计算：对于尚未获取大小的文件，会调用 stat() 获取。
        结果会被缓存，后续访问不再重复计算，直到调用 reset_size_cache()。

        Returns:
            所有文件的总字节数。
        """
        with self._lock:
            keys = list(self._paths)
        return sum(self._get_bytes(key) for key in keys)

    @property
    def total_size(self) -> FileSize:
        """获取总文件大小的 FileSize 对象。

        便于格式化输出（如 "1.5 GB"）。

        Returns:
            FileSize 对象，包含总字节数和格式化方法。
        """
        return FileSize(self.total_bytes)

    def reset_size_cache(self) -> None:
        """清除所有已缓存的文件大小。

        调用后，下次访问 total_bytes 时会重新计算所有文件的大小。
        适用于文件内容可能发生变化的场景。
        """
        with self._lock:
            for k, v in self._bytes.items():
                if v is not None:
                    self._bytes[k] = None

    def clear(self) -> None:
        """清空文件列表和大小缓存。

        调用后列表为空，所有已缓存的大小也被清除。
        """
        with self._lock:
            self._paths.clear()
            self._bytes.clear()
