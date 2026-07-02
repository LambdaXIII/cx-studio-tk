"""cx-系列主题预设。

供 cxalio-studio-tools 使用，定义 cx.* 命名空间的样式。
纯数据，不引入依赖。
"""

from rich.theme import Theme

BASE_STYLES: dict[str, str] = {
    "cx.success": "bold green",
    "cx.error": "bold red",
    "cx.warning": "bold yellow",
    "cx.info": "cyan",
    "cx.whisper": "dim",
    "cx.number": "cyan",
}

CX_STYLES: dict[str, str] = BASE_STYLES

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

DETAIL_STYLES: dict[str, str] = {
    "cx.detail.key": "bold",
    "cx.detail.none": "dim",
    "cx.detail.sub_box_border": "grey70",
    "cx.detail.empty": "dim yellow",
}

INDEXED_LIST_STYLES: dict[str, str] = {
    "cx.indexed_list.index": "cyan",
    "cx.indexed_list.empty": "dim",
    "cx.indexed_list.subtitle": "dim",
}

FULL_HELP_STYLES: dict[str, str] = {**BASE_STYLES, **HELP_STYLES}

default_theme = Theme(
    {
        **BASE_STYLES,
        **HELP_STYLES,
        **DETAIL_STYLES,
        **INDEXED_LIST_STYLES,
    }
)

__all__ = [
    "BASE_STYLES",
    "CX_STYLES",
    "HELP_STYLES",
    "DETAIL_STYLES",
    "INDEXED_LIST_STYLES",
    "FULL_HELP_STYLES",
    "default_theme",
]
