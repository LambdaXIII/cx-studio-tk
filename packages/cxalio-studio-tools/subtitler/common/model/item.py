"""字幕条目（SubtitleItem）——模型的原子单元。

定义不依赖任何格式与容器的最小字幕实体：时间范围、台词内容、说话人与
格式扩展位。条目是普通对象，容器只持有其引用。
"""

from dataclasses import dataclass, field
from typing import Any

from cx_studio.core import CxTime, TimeRange

__all__ = ["SubtitleItem"]


@dataclass(frozen=True)
class SubtitleItem:
    """字幕条目：一条带时间范围的台词。

    条目不依附于任何容器——容器持有其引用，同一实例可同时被多个容器引用，
    也可独立创建、独立存在、跨容器流转；引用语义下容器不改变条目状态。

    时间只以 ``TimeRange`` 承载，起点与时长是它的派生只读视图，不重复存储。
    ``frozen`` 仅阻止字段重绑，而 ``TimeRange`` 本身可变，因此改写已入容器的
    条目的时间范围是合法操作，容器在读取时消化这种改写。

    ``extra`` 是格式扩展位：模型不解释、不校验其内容，键的格式前缀约定
    （如 ``ttml_style``）由格式侧遵守。

    Args:
        time_range: 条目的时间范围（起点 + 时长）。
        text: 台词内容，保留真实换行符。
        speaker: 说话人；来源格式无说话人语法时为 None。
        extra: 格式扩展位；键带格式前缀，模型不解释其内容。
    """

    time_range: TimeRange
    text: str
    speaker: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def start(self) -> CxTime:
        """返回条目起始时刻（委托 ``time_range`` 的派生视图）。

        Returns:
            CxTime: 起始时刻。
        """
        return self.time_range.start

    @property
    def duration(self) -> CxTime:
        """返回条目持续时长（委托 ``time_range`` 的派生视图）。

        Returns:
            CxTime: 持续时长。
        """
        return self.time_range.duration
