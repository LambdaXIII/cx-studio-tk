"""Mission 模块 - 转码任务值对象。

提供 Mission、InputSpec、OutputSpec 三个核心类型，用于描述完全解析的转码任务。
"""

from .mission import Mission
from .specs import InputSpec, OutputSpec

__all__ = ["Mission", "InputSpec", "OutputSpec"]
