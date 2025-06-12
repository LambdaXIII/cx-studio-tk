import re

from jpegger.simple_appcontext import SimpleAppContext
from .filters import (
    ImageFilterChain,
    AutoResizeFilter,
    AutoScaleFilter,
    ColorSpaceFilter,
)


class SimpleFilterChainBuilder:

    @staticmethod
    def __parse_size_str(size_str: str | None) -> tuple[int, int] | None:
        if size_str is None:
            return None

        size_str = size_str.strip()
        NUMBER_PAT = r"(\d+)[^\d]+(\d+)"
        match = re.match(NUMBER_PAT, size_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None

    @staticmethod
    def build_filter_chain_from_simple_context(
        app_context: SimpleAppContext,
    ) -> ImageFilterChain:
        filters = []
        if app_context.scale_factor:
            filters.append(AutoScaleFilter(float(app_context.scale_factor)))
        else:
            iw, ih = SimpleFilterChainBuilder.__parse_size_str(app_context.size) or (
                None,
                None,
            )
            if app_context.width and not iw:
                iw = int(app_context.width)
            if app_context.height and not ih:
                ih = int(app_context.height)
            filters.append(AutoResizeFilter(iw, ih))

        if app_context.color_space:
            filters.append(ColorSpaceFilter(app_context.color_space))

        return ImageFilterChain(filters)
