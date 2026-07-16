"""cx-系列主题预设。

供 cxalio-studio-tools 使用，定义 cx.* 命名空间的样式。
纯数据，不引入依赖。

设计意图：cx_wealthy 提供一套 cx 主题作为 tools 的统一预设，
但主体功能仍是 Rich 原生能力——第三方使用方可选择是否应用 ``default_theme``。
"""

from rich.theme import Theme

BASE_STYLES: dict[str, str] = {
    # cx 系列基础接口样式（info/debug/warning/error 等公共约定）
    "cx.info": "cyan",
    "cx.debug": "bright_black",
    "cx.warning": "bold yellow",
    "cx.error": "bold red",
    "cx.argument": "bold green1",
    "cx.success": "bold green",
    "cx.whisper": "dim",
    "cx.number": "cyan",
    "cx.brackets": "magenta",
    "cx.quotes": "light_pink1",
    "cx.filepath": "bold cyan underline",
}

CX_STYLES: dict[str, str] = BASE_STYLES

HELP_STYLES: dict[str, str] = {
    "cx.help.usage.title": "green",  # usage 面板标题
    "cx.help.usage.prog": "orange1",  # 程序名
    "cx.help.usage.bracket": "bright_black",  # 方括号和 pipe 分隔符
    "cx.help.usage.option": "cyan",  # 选项名（如 -o）
    "cx.help.usage.argument": "italic yellow",  # 参数占位符（如 DIR）
    "cx.help.group.title": "orange1",  # 参数分组标题
    "cx.help.group.description": "italic dim default",  # 分组描述
    "cx.help.details.box": "blue",  # 面板边框
    "cx.help.details.description": "italic default",  # 参数描述文本
    "cx.help.usage.command": "bold magenta",  # 命令关键词（如 list）
    "cx.help.epilog": "dim italic default",  # 尾部链接
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
