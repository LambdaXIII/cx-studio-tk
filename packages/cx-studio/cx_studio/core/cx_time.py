"""毫秒精度的时间值对象（CxTime）及其时间码/时间戳换算。

CxTime 以整数毫秒为内部存储，提供 total_* 全量换算、日/时/分/秒/毫秒
分解访问，以及与 Timebase 配合的时间码（timecode）和字符串时间戳
（timestamp）互转。
"""

import re

from .cx_timebase import Timebase
from cx_studio.i18n import _


class CxTime:
    """以整数毫秒为唯一内部状态的时间值对象。

    构造时把入参经 ``int()`` 归一为毫秒整数（即 total_milliseconds），
    支持负值（表示 0 时刻之前的时长/时刻）。

    关键语义约定：
        - 比较运算：``==``/``!=``/``<``/``<=`` 先特判与整数 ``0`` 的
          比较，把 ``0`` 视作零时长（``t == 0`` 等价于毫秒总数为 0，
          ``t < 0`` 等价于毫秒总数为负）；与另一个 CxTime 比较时按
          毫秒总数逐毫秒比较；与其它类型比较一律抛出
          ``NotImplementedError``。
        - 算术运算：``+``/``-`` 要求两个 CxTime；``*``/``/`` 接受
          int/float（``/`` 的结果按 round() 取整）；均返回新的
          CxTime，类型不符抛出 ``NotImplementedError``。
        - 分解访问：days/hours/minutes/seconds/milliseconds 基于
          Python 整除与取模得到各时间单位段（小时及以下对 24/60
          取模，不做整日进位累加；负值会呈现“借位”式分解结果）。
        - ``pretty_string``：自大到小仅输出数值非零的 日/小时/分/秒 段
          并直接拼接（无分隔符）；毫秒段仅在“毫秒余数非零且总时长为负”
          时附加输出，因此正数且不足 1 秒的时长得到空字符串。
        - 文本解析/格式化：``from_timestamp`` 的文本为
          ``HH:MM:SS`` 后随 ``:;.,`` 之一与若干数字，末段直接作为毫秒；
          ``from_timecode``/``to_timecode`` 与 Timebase 配合，按
          “帧 = 秒内毫秒 ÷ 1000 × fps（round 取整）”换算；
          drop_frame 只决定 timecode 的帧分隔符（``;`` 而非 ``:``），
          不做丢帧补偿。
        - 实例可哈希（基于毫秒值），copy/deepcopy 返回等值新实例。
    """

    __TC_PATTERN = r"(\d{2}):(\d{2}):(\d{2})[:;.,](\d+)"

    def __init__(self, milliseconds: int):
        self.__milliseconds = int(milliseconds)

    @property
    def total_milliseconds(self):
        """总时长（毫秒）。

        Returns:
            int: 内部存储的毫秒总数，可为负。
        """
        return self.__milliseconds

    @property
    def total_seconds(self):
        """总时长（秒）。

        Returns:
            float: 毫秒总数 ÷ 1000。
        """
        return self.__milliseconds / 1000.0

    @property
    def total_minutes(self):
        """总时长（分钟）。

        Returns:
            float: 总秒数 ÷ 60。
        """
        return self.total_seconds / 60.0

    @property
    def total_hours(self):
        """总时长（小时）。

        Returns:
            float: 总分钟数 ÷ 60。
        """
        return self.total_minutes / 60.0

    @property
    def total_days(self):
        """总时长（天）。

        Returns:
            float: 总小时数 ÷ 24。
        """
        return self.total_hours / 24.0

    @property
    def milliseconds(self):
        """毫秒段（不足 1 秒的余数部分）。

        Returns:
            int: 毫秒总数对 1000 取模，取值 0~999。
        """
        return self.__milliseconds % 1000

    @property
    def seconds(self):
        """秒段。

        Returns:
            int: 毫秒总数 ÷ 1000 后对 60 取模，取值 0~59。
        """
        return self.__milliseconds // 1000 % 60

    @property
    def minutes(self):
        """分钟段。

        Returns:
            int: 毫秒总数 ÷ 60000 后对 60 取模，取值 0~59。
        """
        return self.__milliseconds // 1000 // 60 % 60

    @property
    def hours(self):
        """小时段（对 24 取模，不累计整天）。

        Returns:
            int: 毫秒总数 ÷ 3600000 后对 24 取模，取值 0~23。
        """
        return self.__milliseconds // 1000 // 60 // 60 % 24

    @property
    def days(self):
        """整天数（对小时取模后的进位部分）。

        Returns:
            int: 毫秒总数 ÷ 86400000 向下取整，可为负。
        """
        return self.__milliseconds // 1000 // 60 // 60 // 24

    def __eq__(self, other):
        if other == 0:
            return self.total_milliseconds == 0
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot compare Time with other types")
        return self.total_milliseconds == other.total_milliseconds

    def __ne__(self, other):
        if other == 0:
            return self.total_milliseconds != 0
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot compare Time with other types")
        return self.total_milliseconds != other.total_milliseconds

    def __lt__(self, other):
        if other == 0:
            return self.total_milliseconds < 0
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot compare Time with other types")
        return self.total_milliseconds < other.total_milliseconds

    def __le__(self, other):
        if other == 0:
            return self.total_milliseconds <= 0
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot compare Time with other types")
        return self.total_milliseconds <= other.total_milliseconds

    def __hash__(self):
        return hash(self.__milliseconds)

    def __copy__(self):
        return CxTime(self.__milliseconds)

    def __deepcopy__(self, memo):
        return CxTime(self.__milliseconds)

    @property
    def pretty_string(self):
        """格式化为按中文单位拼接的可读时长字符串。

        输出规则：
            1. 自大到小依次检查 日/小时/分/秒 各段，仅拼接数值非零的段，
               段与段之间无分隔符，单位文字经 i18n 翻译（如 ``1日2小时3分4秒``）；
            2. 毫秒段仅当毫秒余数非零且总时长为负时附加输出（代码条件为
               ``self.milliseconds > 0 > self.total_minutes``）；
            3. 若上述各段均为零则返回空字符串（正数且不足 1 秒的时长
               即得到空串）。

        Returns:
            str: 拼接后的可读时长文本。
        """
        parts = []
        if self.days > 0:
            parts.append(f"{self.days}{_('日')}")
        if self.hours > 0:
            parts.append(f"{self.hours}{_('小时')}")
        if self.minutes > 0:
            parts.append(f"{self.minutes}{_('分')}")
        if self.seconds > 0:
            parts.append(f"{self.seconds}{_('秒')}")
        if self.milliseconds > 0 > self.total_minutes:
            parts.append(f"{self.milliseconds}{_('毫秒')}")
        return "".join(parts)

    def __add__(self, other):
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot add Time with other types")
        return CxTime(self.total_milliseconds + other.total_milliseconds)

    def __sub__(self, other):
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot subtract Time with other types")
        return CxTime(self.total_milliseconds - other.total_milliseconds)

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            raise NotImplementedError("Cannot multiply Time with other types")
        return CxTime(int(self.total_milliseconds * other))

    def __truediv__(self, other):
        if not isinstance(other, (int, float)):
            raise NotImplementedError("Cannot divide Time with other types")
        return CxTime(int(round(self.total_milliseconds / other)))

    @classmethod
    def from_milliseconds(cls, milliseconds: int):
        """从毫秒数构造实例。

        Args:
            milliseconds: 毫秒数（可为负）。

        Returns:
            CxTime: 直接以该毫秒数构造的实例。
        """
        return cls(milliseconds)

    @classmethod
    def from_seconds(cls, seconds: float):
        """从秒数构造实例。

        Args:
            seconds: 秒数（可为小数、负数）。

        Returns:
            CxTime: 秒数 × 1000 后按 round() 取整得到的实例。
        """
        return cls(round(seconds * 1000))

    @classmethod
    def from_minutes(cls, minutes: float):
        """从分钟数构造实例。

        Args:
            minutes: 分钟数（可为小数、负数）。

        Returns:
            CxTime: 分钟数 × 60000 后按 round() 取整得到的实例。
        """
        return cls(round(minutes * 60 * 1000))

    @classmethod
    def from_hours(cls, hours: float):
        """从小时数构造实例。

        Args:
            hours: 小时数（可为小数、负数）。

        Returns:
            CxTime: 小时数 × 3600000 后按 round() 取整得到的实例。
        """
        return cls(round(hours * 60 * 60 * 1000))

    @classmethod
    def from_days(cls, days: float):
        """从天数构造实例。

        Args:
            days: 天数（可为小数、负数）。

        Returns:
            CxTime: 天数 × 86400000 后按 round() 取整得到的实例。
        """
        return cls(round(days * 24 * 60 * 60 * 1000))

    @classmethod
    def zero(cls):
        """构造零时长实例。

        Returns:
            CxTime: 毫秒总数为 0 的实例。
        """
        return cls(0)

    @classmethod
    def one_second(cls):
        """构造 1 秒时长的实例。

        Returns:
            CxTime: 时长为 1000 毫秒的实例。
        """
        return cls.from_seconds(1)

    def to_timestamp(self) -> str:
        """格式化为 ``HH:MM:SS.mmm`` 时间戳字符串。

        时/分/秒取自已对 24/60 取模的分解属性（不含 days 段），
        毫秒固定补零到 3 位。

        Returns:
            str: 形如 ``01:02:03.004`` 的时间戳文本。
        """
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}.{self.milliseconds:03d}"

    def to_timecode(self, timebase: Timebase) -> str:
        """按时间基准格式化为时间码字符串。

        帧号 = 秒内毫秒（milliseconds）÷ 1000 × fps，四舍五入后补零到
        fps 十进制位数；帧分隔符在 ``timebase.drop_frame`` 为真时用
        ``;``，否则用 ``:``（仅分隔符差异，不做丢帧补偿）。

        Args:
            timebase: 提供 fps 与 drop_frame 标记的时间基准。

        Returns:
            str: 形如 ``01:02:03:12`` 的时间码文本。
        """
        sep = ";" if timebase.drop_frame else ":"
        ff = self.milliseconds / 1000.0 * timebase.fps
        ff_digits = len(str(timebase.fps))
        ff_str = f"{round(ff):0{ff_digits}d}"
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}{sep}{ff_str}"

    @classmethod
    def from_timestamp(cls, ts: str):
        """从时间戳字符串解析实例。

        用正则 ``(\\d{2}):(\\d{2}):(\\d{2})[:;.,](\\d+)`` 从文本开头匹配：
        时/分/秒各两位，其后为 ``:;.,`` 之一与任意位数数字，末段直接作为
        毫秒值（不按三位补零换算，如 ``.5`` 表示 5 毫秒）；匹配到合法前缀
        后忽略其余内容（前缀匹配，非全串匹配）。

        Args:
            ts: 形如 ``00:00:01.500`` 的时间戳文本。

        Returns:
            CxTime: 解析得到的时间实例。

        Raises:
            ValueError: 文本开头不匹配上述格式时。
        """
        match = re.match(CxTime.__TC_PATTERN, ts)
        if not match:
            raise ValueError(f"Invalid timestamp format: {ts}")
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        milliseconds = int(match.group(4))
        return cls(hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds)

    @classmethod
    def from_timecode(cls, tc: str, timebase: Timebase):
        """从时间码字符串解析实例。

        正则同 from_timestamp，但末段数字按帧数处理并换算为毫秒：
        ``毫秒 = round(帧数 ÷ fps × 1000)``。drop_frame 不影响本方法
        （帧一律按整帧换算，不做丢帧补偿）。

        Args:
            tc: 形如 ``00:00:01:12`` 的时间码文本。
            timebase: 提供 fps 的时间基准。

        Returns:
            CxTime: 解析得到的时间实例。

        Raises:
            ValueError: 文本开头不匹配上述格式时。
        """
        match = re.match(CxTime.__TC_PATTERN, tc)
        if not match:
            raise ValueError(f"Invalid timecode format: {tc}")
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        frames = int(match.group(4))
        milliseconds = int(round(frames / timebase.fps * 1000))
        return cls(hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds)
