from collections.abc import Callable
from pathlib import Path

from cx_studio.core.cx_filesize import FileSize

from .path_expander import PathExpander


class FileSizer:
    """文件大小计算器。

    支持自定义大小计算策略，推荐通过注入 sizer_function 实现缓存、
    权限处理、特殊文件类型等高级功能。

    推荐做法：
        手工提供 sizer_function 而非依赖 default_sizer，尤其是在需要
        重复查询相同路径或处理大规模文件列表时。自定义 sizer 应引入
        缓存能力（如 functools.lru_cache 或 FileInfoCache）以避免重复
        调用 stat() 系统调用。

    示例：
        >>> from functools import lru_cache
        >>> from pathlib import Path
        >>> from cx_studio.filesystem.cx_file_sizer import FileSizer
        >>>
        >>> @lru_cache(maxsize=1024)
        ... def cached_sizer(path: Path) -> int:
        ...     if not (path.is_file() or path.is_dir()):
        ...         return 0
        ...     if path.is_file():
        ...         return path.stat().st_size
        ...     # 目录：递归累加子文件大小
        ...     return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
        >>>
        >>> sizer = FileSizer(cached_sizer)
        >>> sizer.get_bytes(Path("some_file.txt"))
    """

    def __init__(self, sizer_function: Callable[[Path], int] | None = None) -> None:
        """初始化文件大小计算器。

        Args:
            sizer_function: 自定义大小计算函数，接收 Path 返回字节数。
                None 时使用 default_sizer（简单实现，无缓存）。
                推荐注入带缓存的自定义函数以提升性能。
        """
        self._sizer: Callable[[Path], int] = sizer_function or self.default_sizer

    @staticmethod
    def default_sizer(path: Path) -> int:
        """默认大小计算函数。

        简单实现，**不推荐在生产环境直接使用**，仅作为兜底。

        行为：
            - 普通文件：返回 path.stat().st_size
            - 目录：递归遍历所有子文件并累加大小
            - 不存在或非文件/目录（如设备文件、FIFO）：返回 0
            - 权限不足或访问异常：返回 0（静默跳过）

        局限性：
            - 无缓存，重复查询同一路径会重复调用 stat()
            - 目录大小计算为 O(n)，大目录下性能差
            - 不支持符号链接解析控制

        Args:
            path: 待计算大小的路径。

        Returns:
            文件或目录的字节大小；无法计算时返回 0。
        """

        def _try_get_size(p: Path) -> int:
            try:
                return p.stat().st_size
            except OSError:
                return 0

        if not (path.is_file() or path.is_dir()):
            return 0
        if path.is_file():
            return _try_get_size(path)
        expander = PathExpander(PathExpander.StartInfo(accept_dirs=False))
        dir_size = 0
        for p in expander.expand(path):
            dir_size += _try_get_size(p)
        return dir_size

    def get_bytes(self, path: Path) -> int:
        """获取路径的字节大小。

        通过注入的 sizer_function 计算，行为由 sizer_function 决定。

        Args:
            path: 待计算大小的路径。

        Returns:
            字节大小；无法计算时返回 0。
        """
        return self._sizer(path)

    def get_file_size(self, path: Path) -> FileSize:
        """获取路径的文件大小对象。

        将 get_bytes() 的结果包装为 FileSize 值对象，便于格式化输出。

        Args:
            path: 待计算大小的路径。

        Returns:
            FileSize 对象，包含字节大小和格式化方法。
        """
        return FileSize(self.get_bytes(path))
