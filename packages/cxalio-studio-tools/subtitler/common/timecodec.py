"""模式驱动的字幕时间换算。

TimeCodec 把「时间模式」与「时间值」的互转集中到一处：格式实现各自声明
自己格式的时间模式（如 ``HH:MM:SS,mmm``），解析、格式化与精度取整都经本类
完成，格式实现不再各自手写正则与补零逻辑。
"""

import re
from dataclasses import dataclass

from cx_studio.core import CxTime

from .errors import FormatError

_TOKEN_SCANNER = re.compile(r"mmm|HH|MM|SS|H|M|S")

_UNIT_MILLISECONDS = {
    "H": 3_600_000,
    "M": 60_000,
    "S": 1_000,
    "ms": 1,
}


@dataclass(frozen=True)
class _Token:
    """模式中的一个时间字段占位符。

    Attributes:
        kind: 字段类型，``"H"``/``"M"``/``"S"``/``"ms"`` 之一。
        width: 定宽字段的输出宽度；变宽字段为 None（输出不加前导零）。
    """

    kind: str
    width: int | None

    def to_regex(self) -> str:
        """返回本字段的匹配片段。

        Returns:
            str: 定宽字段为恰 width 位数字，变宽字段为一至两位数字。
        """
        if self.width is None:
            return r"\d{1,2}"
        return rf"\d{{{self.width}}}"

    def render(self, number: int) -> str:
        """按字段宽度渲染数值。

        Args:
            number: 字段数值。

        Returns:
            str: 定宽字段补前导零到 width 位，变宽字段按最短十进制输出。
        """
        if self.width is None:
            return str(number)
        return f"{number:0{self.width}d}"


class TimeCodec:
    """按固定模式解析、渲染与取整字幕时间。

    模式由字段 token 与任意字面分隔符组成：

    - ``HH``/``MM``/``SS``——恰两位数字的时/分/秒；``H``/``M``/``S``——一至
      两位数字的同名字段（``1`` 与 ``01`` 皆接受，输出不加前导零）
    - ``mmm``——恰三位数字的毫秒
    - 其余字符一律按字面匹配与输出（无需转义），如 ``:``、``,``、``.``

    字段值域不做校验：分/秒等字段允许超过 59，模式同样用于表达时长与偏移量
    字面量；严格性只针对字面形态。解析要求整串匹配，不做前缀匹配，也不做
    宽松兜底。

    本类不复用 ``CxTime.from_timestamp``：后者用正则从文本开头前缀匹配并忽略
    其余内容，且末段数字直接当作毫秒（``.5`` 表示 5 毫秒而非 500 毫秒），与
    格式契约要求的「全串严格匹配 + 定宽字段」不符。
    """

    def __init__(self, pattern: str) -> None:
        """按模式编译解析正则与字段布局。

        Args:
            pattern: 时间模式文本，至少含一个字段 token。

        Raises:
            ValueError: pattern 为空或不含任何字段 token。模式是使用方的
                编程期常量而非来源数据，故此处的非法模式按编程错误处理，
                不抛 FormatError。
        """
        segments: list[_Token | str] = []
        position = 0
        while position < len(pattern):
            match = _TOKEN_SCANNER.match(pattern, position)
            if match is None:
                segments.append(pattern[position])
                position += 1
                continue
            text = match.group()
            if text == "mmm":
                segments.append(_Token("ms", 3))
            else:
                segments.append(_Token(text[0], 2 if len(text) == 2 else None))
            position += len(text)

        tokens = [segment for segment in segments if isinstance(segment, _Token)]
        if not tokens:
            raise ValueError(f"时间模式不含任何字段 token：{pattern!r}")

        self._pattern = pattern
        self._segments: tuple[_Token | str, ...] = tuple(segments)
        self._tokens = tuple(tokens)
        regex_parts: list[str] = []
        for segment in segments:
            if isinstance(segment, _Token):
                regex_parts.append(f"({segment.to_regex()})")
            else:
                regex_parts.append(re.escape(segment))
        self._regex = re.compile("".join(regex_parts))
        self._unit_milliseconds = _UNIT_MILLISECONDS[tokens[-1].kind]

    @property
    def unit_milliseconds(self) -> int:
        """模式精度单位的毫秒数。

        由模式最后一个字段 token 决定：``mmm`` 为 1、``S``/``SS`` 为 1000、
        ``M``/``MM`` 为 60000、``H``/``HH`` 为 3600000。

        Returns:
            int: 精度单位的毫秒数。
        """
        return self._unit_milliseconds

    def parse(self, text: str) -> CxTime:
        """按模式严格解析时间文本。

        整串必须与模式相符（正则全匹配，而非前缀匹配）；不匹配即抛
        FormatError，不做宽松兜底。字段值域不校验，见类说明。

        Args:
            text: 待解析的时间文本。

        Returns:
            CxTime: 解析得到的时间值。

        Raises:
            FormatError: 文本与模式不符。
        """
        match = self._regex.fullmatch(text)
        if match is None:
            raise FormatError(f"时间文本与模式 {self._pattern!r} 不符：{text!r}")
        total_milliseconds = sum(
            int(raw) * _UNIT_MILLISECONDS[token.kind]
            for token, raw in zip(self._tokens, match.groups(), strict=True)
        )
        return CxTime(total_milliseconds)

    def format(self, value: CxTime) -> str:
        """按模式渲染时间值。

        渲染按模式粒度向下截断（低于精度的余量丢弃，如模式无 ``mmm`` 时毫秒
        被舍去）；需要对齐到模式精度时，先用 round_to_unit 取整。字段宽度
        遵循模式：定宽字段补前导零，变宽字段不加前导零；负值整体带负号输出。

        Args:
            value: 待渲染的时间值。

        Returns:
            str: 与模式相符的时间文本。
        """
        total_milliseconds = value.total_milliseconds
        sign = "-" if total_milliseconds < 0 else ""
        magnitude = abs(total_milliseconds)
        numbers = {
            "H": magnitude // 3_600_000,
            "M": magnitude // 60_000 % 60,
            "S": magnitude // 1_000 % 60,
            "ms": magnitude % 1_000,
        }
        rendered = "".join(
            (
                segment.render(numbers[segment.kind])
                if isinstance(segment, _Token)
                else segment
            )
            for segment in self._segments
        )
        return sign + rendered

    def round_to_unit(self, value: CxTime) -> CxTime:
        """把时间值向下取整到模式精度单位。

        以 unit_milliseconds 为步长做地板取整（负数向负无穷取整）。地板取整
        是单调不减映射：取整前后任意两个时间值的大小关系保持不变，因此批量
        换算到更粗精度的格式时不会颠倒 Item 的先后顺序——这正是选择向下取整
        而非四舍五入的原因，四舍五入会把相邻时间推向相反方向。

        Args:
            value: 待取整的时间值。

        Returns:
            CxTime: 取整后的新实例；输入已是单位整数倍时与原值等值。
        """
        total_milliseconds = value.total_milliseconds
        return CxTime(total_milliseconds - total_milliseconds % self._unit_milliseconds)
