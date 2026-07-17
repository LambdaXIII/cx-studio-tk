"""从 `SimpleAppContext` 构建 `ImageFilterChain`。

本模块负责将命令行参数中的尺寸与色彩空间选项翻译为具体的
`IImageFilter` 实例。缩放相关参数按以下优先级处理：

1. `--scale`：等比例缩放。
2. `--size`：指定目标宽高，居中裁剪。
3. `--width` / `--height`：单独指定某一边，另一边保持比例。
"""

import re

from jpegger.simple_appcontext import SimpleAppContext

from .filters import (
    AutoResizeFilter,
    AutoScaleFilter,
    ColorSpaceFilter,
    IImageFilter,
    ImageFilterChain,
)


class SimpleFilterChainBuilder:
    """基于简单应用上下文构建图像过滤器链。"""

    @staticmethod
    def __parse_size_str(size_str: str | None) -> tuple[int, int] | None:
        """从 "WIDTHxHEIGHT" 风格字符串解析宽高。

        分隔符可以是任意非数字字符。

        Args:
            size_str: 用户输入的尺寸字符串；None 时返回 None。

        Returns:
            解析后的 (width, height)，无法解析时返回 None。
        """
        if size_str is None:
            return None

        size_str = size_str.strip()
        number_pat = r"(\d+)[^\d]+(\d+)"
        match = re.match(number_pat, size_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None

    @staticmethod
    def build_filter_chain_from_simple_context(
        app_context: SimpleAppContext,
    ) -> ImageFilterChain:
        """根据命令行上下文构建过滤器链。

        优先级：--scale > --size > --width/--height。
        若未指定任何缩放参数，仍会添加一个 `AutoResizeFilter(None, None)`，
        它在运行时是 no-op，但统一了后续处理流程。

        Args:
            app_context: 解析后的命令行上下文。

        Returns:
            构建好的 `ImageFilterChain` 实例。
        """
        filters: list[IImageFilter] = []
        if app_context.scale_factor:
            # 比例缩放优先级最高。
            filters.append(AutoScaleFilter(float(app_context.scale_factor)))
        else:
            # 其次解析显式尺寸。
            iw, ih = SimpleFilterChainBuilder.__parse_size_str(app_context.size) or (
                None,
                None,
            )
            # 命令行 --width/--height 可作为 size 的补充或替代。
            if app_context.width and not iw:
                iw = app_context.width
            if app_context.height and not ih:
                ih = app_context.height
            filters.append(AutoResizeFilter(iw, ih))

        if app_context.color_space:
            filters.append(ColorSpaceFilter(app_context.color_space))

        return ImageFilterChain(filters)
