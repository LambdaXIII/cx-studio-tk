from .image_filter import IImageFilter
from PIL.Image import Image


class ImageFilterChain(IImageFilter):
    def __init__(self, filters: list):
        super().__init__()
        self.filters = filters

    def append(self, filter: IImageFilter):
        self.filters.append(filter)

    def run(self, image: Image) -> Image:
        for filter in self.filters:
            image = filter.run(image)
        return image
