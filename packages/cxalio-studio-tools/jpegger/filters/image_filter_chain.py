from typing import override

from PIL.Image import Image

from .image_filter import IImageFilter


class ImageFilterChain(IImageFilter):
    def __init__(self, filters: list):
        super().__init__()
        self.filters = filters

    def append(self, img_filter: IImageFilter):
        if isinstance(img_filter, ImageFilterChain):
            self.filters.extend(img_filter.filters)
        else:
            self.filters.append(img_filter)

    def run(self, image: Image) -> Image:
        for img_filter in self.filters:
            image = img_filter.run(image)
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
            yield f"[dim cyan]{i} {f.filter_name()}[/]", f.__filter_description__()

    def __filter_description__(self) -> str:
        descriptions = [f.__filter_description__() for f in self.filters]
        return "；".join(descriptions)

    def step_descriptions(self) -> list[str]:
        return [f"{f.filter_name()}:{f.__filter_description__()}" for f in self.filters]

    def __rich_repr__(self):
        for i, f in enumerate(self.filters):
            yield i, f.filter_name(), f.__filter_description__()
