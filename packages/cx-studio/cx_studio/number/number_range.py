class NumberRange:
    def __init__(
        self,
        top: float | int | None = None,
        bottom: float | int | None = None,
        step: float | int = 1,
        default_factory=None,
    ):
        if all([bottom, top]):
            self.bottom = min(bottom, top)
            self.top = max(bottom, top)
        else:
            self.bottom = bottom
            self.top = top

        self.step = step
        self.default_factory = default_factory

    def __format_result(self, x):
        if self.default_factory is None:
            return x
        return self.default_factory(x)

    def iter_numbers(self, step: int | float | None = None):
        step = step or self.step
        x = self.bottom or self.top
        while x <= self.top:
            yield self.__format_result(x)
            x += step

    def contains(self, x: float | int) -> bool:
        result = False
        if self.bottom is not None:
            result = x >= self.bottom
        if self.top is not None:
            result = result and x <= self.top
        return result

    def number_from_percent(self, percent: float | int) -> float | int:
        result = self.bottom + (self.top - self.bottom) * percent
        return self.__format_result(result)

    def percent_from_number(self, x: float | int) -> float | int:
        result = (x - self.bottom) / (self.top - self.bottom)
        return self.__format_result(result)

    def remap_number_to(
        self, x: float | int, other_range: "NumberRange"
    ) -> float | int:
        percent = self.percent_from_number(x)
        result = other_range.number_from_percent(percent)
        return self.__format_result(result)

    def middle_number(self) -> float | int:
        left = self.bottom or self.top
        right = self.top or self.bottom
        if all([self.bottom, self.top]):
            return left + (right - left) / 2
        return left or right or 0

    def clamp(self, x: float | int) -> float | int:
        result = x
        if self.bottom is not None:
            result = max(result, self.bottom)
        if self.top is not None:
            result = min(result, self.top)
        return self.__format_result(result)
