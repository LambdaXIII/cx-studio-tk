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

    def __len__(self):
        return len(self.filters)

    def __rich_label__(self) -> str:
        if len(self.filters) == 0:
            return "[red][EMPTY_FILTER_CHAIN][/]"
        labels = [x.__rich_label__() for x in self.filters]
        return "[dim]=>[/]".join(labels)

    def __rich_detail__(self):
        yield "Filter Chaing"
        for i, f in enumerate(self.filters):
            yield f"[dim cyan]{i}[/]", f.__rich_label__()
