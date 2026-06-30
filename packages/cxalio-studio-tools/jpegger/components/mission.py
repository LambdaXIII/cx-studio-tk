"""Jpegger 任务模型。

`Mission` 描述了一次"源文件 → 目标文件"的图像处理任务，
包含目标格式、过滤器链、保存/加载选项等元信息。
"""

from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ulid

from cx_tools.i18n import _
from ..filters import ImageFilterChain


@dataclass(frozen=True)
class Mission:
    """单次图像处理任务。

    该对象是不可变的（frozen dataclass），可被 MissionRunner 安全地
    在多线程中共享。

    Args:
        source: 源图像路径。
        target: 目标图像路径。
        target_format: 显式指定的 PIL 保存格式名称；None 表示自动推断。
        filter_chain: 应用于源图像的过滤器链。
        saving_options: 透传给 `Image.save()` 的关键字参数。
        load_options: 透传给 `Image.open()` 的关键字参数。
        mission_id: 唯一任务标识，自动生成。
    """

    source: Path
    target: Path
    target_format: str | None
    filter_chain: ImageFilterChain = field(
        default_factory=lambda: ImageFilterChain([]), kw_only=True
    )
    saving_options: dict[str, Any] = field(default_factory=dict, kw_only=True)
    load_options: dict[str, Any] = field(default_factory=dict, kw_only=True)
    mission_id: ulid.ULID = field(default_factory=ulid.new, kw_only=True)

    def __rich_label__(self) -> Generator[str, None, None]:
        """为 `WealthLabel` 提供紧凑的任务标签。"""
        yield f"[yellow]>{self.target_format or 'auto'}[/]"
        yield self.source.name
        yield f"[blue]=={len(self.filter_chain)}=>[/]"
        yield self.target.name

    def __rich_detail__(self) -> Generator[tuple[str, Any], None, None]:
        """为详情面板列出任务的关键信息。"""
        yield _("源文件"), str(self.source)
        yield _("目标文件"), str(self.target)
        yield _("目标格式"), self.target_format or _("自动推断")
        yield _("过滤器链"), self.filter_chain
        yield _("保存选项"), self.saving_options
        yield _("加载选项"), self.load_options
