"""SuffixValidator — 文件后缀匹配验证器。

将一组后缀规范化（统一小写并确保前导点）后，判断路径的后缀是否
命中集合；供 PathExpander 等作为文件过滤器使用。
"""

from collections.abc import Collection
from pathlib import Path
from typing import Iterable

from .path_validator import *


class SuffixValidator(IPathValidator):
    """判定路径后缀是否命中集合的验证器。

    构造时把每个条目转为字符串并规范化：统一小写、缺前导点时补
    "."（如 "txt" 与 ".TXT" 都归为 ".txt"）。validate() 将路径的
    后缀（小写）与集合比较，命中即通过；后缀集合为空时任何路径
    都不通过（恒返回 False）。
    """

    @staticmethod
    def __clear_suffix(suffix: str) -> str:
        result = suffix.lower()
        if not result.startswith("."):
            result = "." + result
        return result

    def __init__(self, suffixes: Collection | Iterable):
        """初始化后缀集合。

        Args:
            suffixes: 可迭代的后缀条目集合，元素可为带或不带前导点
                的字符串（如 "txt"、".TXT"）。
        """
        self.__suffixes = {self.__clear_suffix(str(s)) for s in suffixes}

    def validate(self, path: str | Path) -> bool:
        """判断路径的文件后缀是否命中集合。

        Args:
            path: 待验证的路径（字符串或 Path 对象）。

        Returns:
            路径后缀（小写）属于集合时为 True，否则为 False。
        """
        return Path(path).suffix.lower() in self.__suffixes
