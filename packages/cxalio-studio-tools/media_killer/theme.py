"""media_killer 主题样式。

定义 ``cx.mk.*`` 命名空间下的 Rich 样式，与 ``cx_wealthy.default_theme``
合并后供 media_killer 所有输出组件使用。

设计原则：仅保留标准主题（``cx.*``）无法覆盖的 media_killer 特有语义；
通用语义一律使用标准 token（``cx.info``、``cx.debug``、``cx.whisper`` 等），
避免同一视觉含义散落为多个自定义 token。
"""

from cx_wealthy import default_theme as cx_default_theme
from cx_wealthy import rich_types as r

MEDIA_KILLER_STYLES: dict[str, str] = {
    # Mission 徽章（short_id 前缀标识，media_killer 独有视觉元素）
    "cx.mk.badge": "dim green",
    # 应用 banner
    "cx.mk.banner": "bold red",
    # Mission 标识行：任务名是核心标识符，需与 cx.info（一般信息）区分
    "cx.mk.mission.name": "yellow",
    # 状态（低调非宣告式，区别于 cx.success/cx.error 的 bold 版本）
    "cx.mk.status.success": "green",
    "cx.mk.status.failed": "red",
    "cx.mk.status.canceled": "bright_blue",
}

media_killer_theme = r.Theme({**cx_default_theme.styles, **MEDIA_KILLER_STYLES})

__all__ = ["MEDIA_KILLER_STYLES", "media_killer_theme"]
