from typing import override
from cx_wealth.wealth_label import WealthLabel
from .image_filter import IImageFilter
from PIL.Image import Image


class ImageFilterChain(IImageFilter):
    def __init__(self, filters: list):
        super().__init__()
        self.filters = filters

    def append(self, filter: IImageFilter):
        if isinstance(filter, ImageFilterChain):
            self.filters.extend(filter.filters)
        else:
            self.filters.append(filter)

    def run(self, image: Image) -> Image:
        for filter in self.filters:
            image = filter.run(image)
        return image

    @override
    def filter_name(self):
        return "FilterChain"

    def __len__(self):
        return len(self.filters)

    def __rich_label__(self):
        yield from super().__rich_label__()
        yield f"[blue]({len(self.filters)}Filters)[/]"

    def __rich_detail__(self):
        yield "Filter Chaing"
        for i, f in enumerate(self.filters):
            yield f"[dim cyan]{i}[/]", WealthLabel(f)
