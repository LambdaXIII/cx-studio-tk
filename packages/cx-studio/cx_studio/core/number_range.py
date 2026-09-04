"""数值区间（NumberRange）：一维数值区间上的迭代、判定与映射工具。

支持可选边界（bottom/top 可为 None）、自定义步长与结果转换工厂
（default_factory），提供包含判定、百分比与数值互转、区间到区间的
线性映射、中点与钳制等操作，供参数归一化/映射场景复用。
"""


class NumberRange:
    """一维数值区间值对象。

    构造与字段语义：
        - ``bottom``/``top`` 均可省略（None 表示未设置该侧边界）；
          当两侧都给出时自动取 min/max 归一为 bottom <= top
          （0 是合法边界值，不会因“假值”判定被跳过）。
        - 未设置的一侧按“该侧不设约束”参与 contains/clamp 等判定，
          但部分方法依赖边界存在或存在退化行为，详见各方法 docstring
          及实现。
        - ``step``：迭代步长，默认 1；iter_numbers 未显式传参时使用。
        - ``default_factory``：可选的单参数结果转换函数（如 int、
          round）；作用于 iter_numbers / number_from_percent /
          percent_from_number / remap_number_to / clamp 的返回值，
          middle_number 除外。
    """

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
        """按固定步长从下界向上界迭代区间内的数值（含上界）。

        迭代要求存在可用的上界：top 为 None 时不产出任何值。起点取
        ``bottom or top``——bottom 为 None 或 0 等假值时退化为 top
        （此时只会产出 top 自身）。步长优先取传入的 step，为 None 或 0
        时回退到区间自身的 step。每个产物经 default_factory 处理后产出。

        Args:
            step: 迭代步长；None 或 0 时使用 self.step。

        Yields:
            从起点到 top（含端点）的等距数值。
        """
        step = step or self.step
        x = self.bottom or self.top
        # 无边界时无需迭代
        if x is None or self.top is None:
            return
        while x <= self.top:
            yield self.__format_result(x)
            x += step

    def contains(self, x: float | int) -> bool:
        """判断数值 x 是否落在已设置边界的区间内。

        仅当下界已设置（bottom 非 None）时结果才可能为 True：先按下界
        判 ``x >= bottom``，再在已设置上界时追加 ``x <= top`` 条件。
        下界未设置时恒返回 False（含双侧均未设置的情形）。

        Args:
            x: 待判定的数值。

        Returns:
            bool: x 位于区间内返回 True。
        """
        result = False
        if self.bottom is not None:
            result = x >= self.bottom
        if self.top is not None:
            result = result and x <= self.top
        return result

    def number_from_percent(self, percent: float | int) -> float | int:
        """把 0~1 的相对位置映射为区间内的数值。

        线性换算 ``bottom + (top - bottom) * percent``，percent 越界时
        按同一比例外推。结果经 default_factory 处理后返回。

        Args:
            percent: 区间内的相对位置，通常取 0~1（可越界外推）。

        Returns:
            float | int: 换算得到的数值（可能经 default_factory 转换）。

        Raises:
            AssertionError: bottom 或 top 未设置（为 None）时。
        """
        assert (
            self.bottom is not None and self.top is not None
        ), "Range bounds must be set"
        result = self.bottom + (self.top - self.bottom) * percent  # type: ignore[operator]  # both None-checked above
        return self.__format_result(result)

    def percent_from_number(self, x: float | int) -> float | int:
        """把区间内的数值映射为 0~1 的相对位置（number_from_percent 的逆）。

        线性换算 ``(x - bottom) / (top - bottom)``；x 越界时结果同样
        越出 0~1。结果经 default_factory 处理后返回。

        Args:
            x: 区间内的数值。

        Returns:
            float | int: 换算得到的相对位置（可能经 default_factory 转换）。

        Raises:
            AssertionError: bottom 或 top 未设置（为 None）时。
        """
        assert (
            self.bottom is not None and self.top is not None
        ), "Range bounds must be set"
        result = (x - self.bottom) / (self.top - self.bottom)  # type: ignore[operator]  # both None-checked above
        return self.__format_result(result)

    def remap_number_to(
        self, x: float | int, other_range: "NumberRange"
    ) -> float | int:
        """把 x 在本区间内的相对位置映射到另一区间的对应数值。

        先经 percent_from_number 求 x 在本区间内的相对位置，再经
        other_range.number_from_percent 换算为目标区间的数值，最后结果
        再经本区间的 default_factory 处理（other_range 的转换函数已在
        其 number_from_percent 内生效）。

        Args:
            x: 本区间内的数值。
            other_range: 目标区间，须已设置 bottom 与 top。

        Returns:
            float | int: 目标区间中与 x 相对位置相同的数值
            （可能经 default_factory 转换）。
        """
        percent = self.percent_from_number(x)
        result = other_range.number_from_percent(percent)
        return self.__format_result(result)

    def middle_number(self) -> float | int:
        """返回区间的中点。

        双侧边界均设置时返回 ``left + (right - left) / 2``（即
        (bottom + top) / 2）；仅设置单侧时退化返回该侧边界值；双侧均
        未设置时返回 0。注意 left/right 经 ``bottom or top`` 取值，
        bottom 为 0 等假值时的具体回退行为以代码为准。

        Returns:
            float | int: 中点或退化值。
        """
        left = self.bottom or self.top
        right = self.top or self.bottom
        if self.bottom is not None and self.top is not None:
            return left + (right - left) / 2  # type: ignore[operator]  # both None-checked above
        return left or right or 0

    def clamp(self, x: float | int) -> float | int:
        """把数值 x 钳制到区间内（未设置的边界侧不约束）。

        下界已设置时 ``x = max(x, bottom)``，上界已设置时再
        ``x = min(x, top)``；双侧均未设置时原样返回。结果经
        default_factory 处理后返回。

        Args:
            x: 待钳制的数值。

        Returns:
            float | int: 钳制后的数值（可能经 default_factory 转换）。
        """
        result = x
        if self.bottom is not None:
            result = max(result, self.bottom)
        if self.top is not None:
            result = min(result, self.top)
        return self.__format_result(result)
