"""从 `SimpleAppContext` 构建 `Mission` 列表。

`SimpleMissionBuilder` 接收已经构建好的 `ImageFilterChain` 与命令行
上下文，为每个输入文件生成对应的 `Mission`，包括目标路径、目标格式、
保存选项等。
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cx_studio.filesystem import force_suffix, normalize_path, normalize_suffix
from jpegger.components.format_database import FormatDB, FormatInfo
from jpegger.components.mission import Mission
from jpegger.filters import ImageFilterChain

from .simple_appcontext import SimpleAppContext


class SimpleMissionBuilder:
    """基于简单应用上下文构建任务列表。

    Args:
        filter_chain: 已构建好的图像过滤器链。
        app_context: 解析后的命令行上下文。
    """

    filter_chain: ImageFilterChain
    output_dir: Path
    target_format_info: FormatInfo | None
    target_suffix: str | None
    quality: int | None

    # 需要向 Image.save 传入 saveall=True 的动画格式集合。
    # 对静态格式传入 saveall 可能导致 Pillow 抛出未知参数异常。
    # 注意：Jpegger 的核心是处理单张图片，动画格式也仅处理其第一帧；
    # saveall=True 只是为了避免 Pillow 在保存动画格式时因缺少该参数而报错，
    # 并不代表会保留原始动画的所有帧。
    ANIMATED_FORMATS: frozenset[str] = frozenset({"GIF", "WEBP", "APNG", "MPO"})

    def __init__(
        self,
        filter_chain: ImageFilterChain,
        app_context: SimpleAppContext,
    ):
        self.filter_chain = filter_chain
        self.output_dir = normalize_path(app_context.output_dir or Path.cwd())

        target_format = app_context.target_format
        self.target_format_info = (
            FormatDB.search(target_format) if target_format else None
        )
        self.target_suffix = None
        if self.target_format_info:
            self.target_suffix = normalize_suffix(target_format or "").lower()
            if self.target_suffix not in self.target_format_info.extensions:
                self.target_suffix = self.target_format_info.preferred_extension

        self.quality = app_context.quality

    def make_mission(self, source: Path | str) -> Mission:
        """为单个输入文件构建任务。

        Args:
            source: 输入文件路径或字符串。

        Returns:
            构建好的 `Mission` 实例。
        """
        source = normalize_path(source)
        target = self.output_dir / source.name
        if self.target_suffix:
            target = force_suffix(target, self.target_suffix)

        # 仅对动画格式注入 saveall，避免静态格式报错。
        saving_options: dict[str, Any] = {}
        if (
            self.target_format_info
            and self.target_format_info.name in self.ANIMATED_FORMATS
        ):
            saving_options["saveall"] = True
        if self.quality:
            saving_options["quality"] = self.quality

        # 若格式信息中声明了加载参数，透传给 Image.open。
        load_options: dict[str, Any] = {}
        if self.target_format_info and self.target_format_info.load_params:
            load_options = dict(self.target_format_info.load_params)

        return Mission(
            source=source,
            target=target,
            target_format=(
                self.target_format_info.name if self.target_format_info else None
            ),
            filter_chain=self.filter_chain,
            saving_options=saving_options,
            load_options=load_options,
        )

    def make_missions(self, sources: Sequence[Path | str]) -> list[Mission]:
        """为多个输入文件批量构建任务。

        Args:
            sources: 输入文件路径序列。

        Returns:
            任务实例列表。
        """
        return [self.make_mission(s) for s in sources]
