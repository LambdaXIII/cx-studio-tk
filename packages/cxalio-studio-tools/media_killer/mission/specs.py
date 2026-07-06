"""Mission 的输入/输出规格定义。

InputSpec 和 OutputSpec 描述 Mission 中每个输入/输出文件及其专属选项。
所有路径在构造前必须解析为绝对路径。
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InputSpec:
    """输入文件规格。

    Attributes:
        filename: 输入文件的绝对路径
        options: 该输入文件的专属选项列表
    """

    filename: Path
    options: list[str]


@dataclass(frozen=True)
class OutputSpec:
    """输出文件规格。

    Attributes:
        filename: 输出文件的绝对路径
        options: 该输出文件的专属选项列表
    """

    filename: Path
    options: list[str]
