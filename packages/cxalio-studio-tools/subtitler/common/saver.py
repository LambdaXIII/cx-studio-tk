"""字幕格式写向契约。

SubtitleSaver 是格式侧「Item 集合 → 输出文件」的抽象基类：一个 Saver 代表
一种字幕格式的写出实现，输出如何组织（单文件/多文件、交叠如何处理）是它
自己的事，框架不介入其执行。
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path

from .model import SubtitleItem


class SubtitleSaver(ABC):
    """字幕格式写向：把 Item 集合写到目标路径。

    子类契约：

    - **自主组织输出**：单文件还是多文件、交叠如何分组，都由实现自己决定
      （格式知识归格式本体）；组织后 MUST 保证入参中每个 Item 都被写出，
      不丢片。
    - **输入是流**：只把入参当作 Item 的可迭代序列使用，不读取任何容器
      结构（顺序即 Item 的时序，实现按需自行排序）。
    - **多文件命名**：以目标路径的 stem 加 ``.part<k>`` 后缀命名（k 从 1 起、
      按输出顺序），目录与扩展名跟随目标路径，如 ``out.part2.srt``。
    - **写前一次性预检**：解析出全部目标路径后统一检查是否已存在；任一已
      存在（含派生的 ``.part<k>`` 路径）即抛 FormatError 中止，不写出任何
      文件、不覆盖既有文件。
    - **编码**：所有输出以 UTF-8 写出，不带 BOM。
    - **编号字面**：格式文本自带编号时（如 SubRip 行号），按本实现的组织
      结果逐文件从 1、按 Item 时序重新编号，不沿用来源编号。
    - **返回产出**：返回实际写出的文件路径列表，顺序与写入顺序一致。
    - **时间模式自持**：本格式的时间表示模式是实现内部的常量，格式化经共享
      的 TimeCodec 完成，不进入任何跨组件接口。
    """

    @abstractmethod
    def save(self, items: Iterable[SubtitleItem], target: Path) -> list[Path]:
        """把 Item 集合写出到目标路径。

        Args:
            items: 待写出的 Item 可迭代序列。
            target: 目标文件路径；多文件输出以它为命名基准。

        Returns:
            list[Path]: 实际写出的文件路径列表。

        Raises:
            FormatError: 任一目标路径已存在，或入参内容无法以本格式表达。
            OSError: 目标目录不可写等系统级失败。
        """
        pass
