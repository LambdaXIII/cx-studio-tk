"""数值运算快速工具：无状态的一行式钳制与线性区间映射。

提供 quick_clamp（数值钳制）与 quick_remap（区间线性映射，同 AE 的
linear），均以函数形式暴露、不绑定具体对象，可选 cls 直接转换结果类型。
"""


def quick_clamp(
    x, bottom: float | int | None = None, top: float | int | None = None, cls=None
):
    """把数值 x 钳制到 [bottom, top] 区间内。

    bottom/top 为 None 的一侧不设约束（与 NumberRange.clamp 同语义）。
    ``cls`` 用于把结果包装成指定类型：非 None 时返回 ``cls(result)``
    （如 int 可截断小数），None 时原样返回数值。

    Args:
        x: 待钳制的数值。
        bottom: 下界；None 表示不设下界。
        top: 上界；None 表示不设上界。
        cls: 结果类型/构造器；None 时返回原始数值。

    Returns:
        钳制后的数值；cls 非 None 时为 ``cls(result)``。
    """
    result = x
    if bottom is not None:
        result = max(result, bottom)
    if top is not None:
        result = min(result, top)
    return result if cls is None else cls(result)


def quick_remap(x, in_min, in_max, out_min=0.0, out_max=1.0, cls=float):
    """把数值从输入区间线性映射到输出区间（同 AE 中的 linear）。

    换算公式：
    ``(x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min``，
    即保持 x 在输入区间内的相对位置不变。``cls`` 默认 float 用于构造
    结果（传 None 时原样返回数值）。

    Args:
        x: 输入区间内的数值。
        in_min: 输入区间下界。
        in_max: 输入区间上界。
        out_min: 输出区间下界，默认 0.0。
        out_max: 输出区间上界，默认 1.0。
        cls: 结果类型/构造器；None 时返回原始数值。

    Returns:
        映射后的数值；cls 非 None 时为 ``cls(result)``。
    """
    result = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return result if cls is None else cls(result)
