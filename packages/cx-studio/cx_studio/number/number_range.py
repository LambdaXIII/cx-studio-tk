class NumberRange:
    def __init__(
        self,
        top: float | int | None = None,
        bottom: float | int | None = None,
        step: float | int = 1,
        default_factory=None,
    ):
        # 仅当两者均非 None 时取 min/max；0 是合法数值不应被跳过
        if bottom is not None and top is not None:
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
        # 无边界时无需迭代
        if x is None or self.top is None:
            return
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
        """将百分比映射到数值。要求 bottom 和 top 均非 None。"""
        assert self.bottom is not None and self.top is not None, "Range bounds must be set"
        result = self.bottom + (self.top - self.bottom) * percent  # type: ignore[operator]  # both None-checked above
        return self.__format_result(result)

    def percent_from_number(self, x: float | int) -> float | int:
        """将数值映射到百分比。要求 bottom 和 top 均非 None。"""
        assert self.bottom is not None and self.top is not None, "Range bounds must be set"
        result = (x - self.bottom) / (self.top - self.bottom)  # type: ignore[operator]  # both None-checked above
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
        if self.bottom is not None and self.top is not None:
            return left + (right - left) / 2  # type: ignore[operator]  # both None-checked above
        return left or right or 0

    def clamp(self, x: float | int) -> float | int:
        result = x
        if self.bottom is not None:
            result = max(result, self.bottom)
        if self.top is not None:
            result = min(result, self.top)
        return self.__format_result(result)
