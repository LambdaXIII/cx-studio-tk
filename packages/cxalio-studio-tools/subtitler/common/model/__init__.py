"""字幕模型层：Item/Sequence/Project 三件套。

条目（``SubtitleItem``）是模型的原子单元，序列表（``SubtitleSequence``）是
条目的排列容器，项目（``SubtitleProject``）把条目组织为多个不交叠序列。
模型不认识任何字幕格式，格式扩展经条目的扩展位由格式侧承担。
"""

from .item import *
from .project import *
from .sequence import *

__all__ = ["SubtitleItem", "SubtitleSequence", "SubtitleProject"]
