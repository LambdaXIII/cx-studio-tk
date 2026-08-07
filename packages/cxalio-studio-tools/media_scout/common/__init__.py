"""media_scout 通用能力面，对外提供面。

承载 media_scout 的通用检查器能力（`media_scout.common.inspectors`）。
工具间组合只允许指向本包的 common 出口。
"""

from . import inspectors

__all__ = ["inspectors"]
