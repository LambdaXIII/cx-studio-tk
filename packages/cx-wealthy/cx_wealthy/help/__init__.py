"""帮助系统特化层：Action / HelpGroup / WealthyHelp。

继承自 cx_wealthy.document 的通用核心，增加 help 特化能力。

架构层次（低→高）：
- ``cx_wealthy.document`` — Node/Group/Note/WealthyDocument 树结构和基础渲染
- ``cx_wealthy.help`` — Action/HelpGroup/WealthyHelp CLI 帮助语义
- ``cx_wealthy.theme`` — ``cx.help.*`` 样式预设（可选，由调用方通过 Console(theme=...) 决定）
"""

from .action import Action
from .help import WealthyHelp
from .help_group import HelpGroup

__all__ = ["Action", "HelpGroup", "WealthyHelp"]
