"""SuffixFinder — 按文件后缀展开查找文件的工具。

维护一个规范化（统一小写、确保前导点）的文件后缀集合，并以该集合
为过滤条件，借助 PathExpander 在给定路径下展开出所有匹配的文件。
"""

from pathlib import Path
from typing import Iterable

from .path_expander import PathExpander
from .validators import SuffixValidator


class SuffixFinder:
    """维护文件后缀集合并提供按后缀查找文件的能力。

    后缀在加入集合前统一规范化：去除首尾空白、转为小写，并确保以
    "." 开头（如 "TXT" 与 ".txt" 视为同一后缀）。iter_find() 使用
    独立的 PathExpander 配置执行实际查找。
    """

    def __init__(self, *suffixes: str):
        self._suffixes: set[str] = {self.__format_suffix(s) for s in suffixes}

    @staticmethod
    def __format_suffix(suffix: str) -> str:
        suffix = str(suffix).strip().lower()
        if not suffix.startswith("."):
            suffix = "." + suffix
        return suffix

    @property
    def suffixes(self) -> set[str]:
        """当前维护的后缀集合。

        注意：返回的是内部集合对象本身，调用方直接增删元素不会经过
        规范化处理；如需保证条目格式统一，请使用 add_suffix() /
        remove_suffix()。

        Returns:
            内部后缀集合（元素为规范化后的字符串，如 ".txt"）。
        """
        return self._suffixes

    def add_suffix(self, suffix: str):
        """向集合中加入一个后缀（自动规范化）。

        Args:
            suffix: 原始后缀，如 "TXT" 或 ".txt"。
        """
        suffix = self.__format_suffix(suffix)
        self._suffixes.add(suffix)

    def remove_suffix(self, suffix: str):
        """从集合中移除一个后缀（自动规范化）。

        Args:
            suffix: 原始后缀，如 "TXT" 或 ".txt"。

        Raises:
            KeyError: 集合中不存在该后缀时抛出。
        """
        suffix = self.__format_suffix(suffix)
        self._suffixes.remove(suffix)

    def iter_find(self, path: str | Path, recursive: bool = False) -> Iterable[Path]:
        """在给定路径下查找后缀匹配的文件。

        内部构造 PathExpander 并固定配置：只接受真实存在的文件
        （目录与其他类型一律过滤），后缀集合为空时不设后缀过滤器、
        接受全部文件；expand_subdir 由 recursive 控制，因此起点为
        目录且 recursive=False 时不会产出任何结果（目录本身被拒收、
        后代不被展开），起点为文件时直接按后缀判定该文件。

        Args:
            path: 查找起点，可为文件或目录。
            recursive: True 时递归展开起点目录的全部子目录。

        Yields:
            后缀命中集合的文件 Path；展开顺序为深度优先。
        """
        expander = PathExpander()
        expander.start_info.expand_subdir = recursive
        expander.start_info.accept_files = True
        expander.start_info.accept_dirs = False
        expander.start_info.accept_others = False
        expander.start_info.existed_only = True
        expander.start_info.follow_symlinks = True
        if self._suffixes:
            expander.start_info.file_validator = SuffixValidator(self._suffixes)
        yield from expander.expand(path)
