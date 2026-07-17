"""media_killer 主题样式。

定义 ``cx.mk.*`` 命名空间下的 Rich 样式，与 ``cx_wealthy.default_theme``
合并后供 media_killer 所有输出组件使用。
"""

from rich.theme import Theme
from cx_wealthy import default_theme as cx_default_theme

MEDIA_KILLER_STYLES: dict[str, str] = {
    # Mission 标识行
    "cx.mk.mission.type": "bold bright_black",
    "cx.mk.mission.counter": "bright_black",
    "cx.mk.mission.metadata": "dim green",
    "cx.mk.mission.name": "yellow",
    # Preset 标识（与 cx.mk.mission.name 对称：预设名 cyan / 任务名 yellow）
    "cx.mk.preset.name": "cyan",
    "cx.mk.mission.source_dir": "bright_black",
    # 状态
    "cx.mk.status.success": "green",
    "cx.mk.status.failed": "red",
    "cx.mk.status.canceled": "bright_blue",
    "cx.mk.status.running": "yellow",
    # 模式标签
    "cx.mk.mode.overwrite": "red",
    "cx.mk.mode.no_overwrite": "green",
    # Banner
    "cx.mk.banner": "bold red",
}

media_killer_theme = Theme({**cx_default_theme.styles, **MEDIA_KILLER_STYLES})

__all__ = ["MEDIA_KILLER_STYLES", "media_killer_theme"]
