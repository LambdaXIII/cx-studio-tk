"""cx-系列主题预设。

供 cxalio-studio-tools 使用，定义 cx.* 命名空间的样式。
纯数据，不引入依赖。
"""

from rich.theme import Theme

# cx.* 样式定义（被 cxalio-studio-tools 的 IAppEnvironment 使用）
CX_STYLES: dict[str, str] = {
    "cx.success": "bold green",
    "cx.error": "bold red",
    "cx.warning": "bold yellow",
    "cx.info": "cyan",
    "cx.whisper": "dim",
    "cx.number": "cyan",
}

# WealthyHelp 的帮助样式
HELP_STYLES: dict[str, str] = {
    "cx.help.usage.title": "green",
    "cx.help.usage.prog": "orange1",
    "cx.help.usage.bracket": "bright_black",
    "cx.help.usage.option": "cyan",
    "cx.help.usage.argument": "italic yellow",
    "cx.help.group.title": "orange1",
    "cx.help.group.description": "italic dim default",
    "cx.help.details.box": "blue",
    "cx.help.details.description": "italic default",
    "cx.help.epilog": "dim italic default",
}

default_theme = Theme({**CX_STYLES, **HELP_STYLES})

__all__ = ["CX_STYLES", "HELP_STYLES", "default_theme"]
