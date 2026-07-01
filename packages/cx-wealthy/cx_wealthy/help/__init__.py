"""帮助系统特化层：Action / WealthyHelp。

继承自 cx_wealthy.document 的通用核心，增加 help 特化能力。
"""

from .action import Action
from .help import WealthyHelp

__all__ = ["Action", "WealthyHelp"]
