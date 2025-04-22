import gettext
import os
import re

from .cx_timebase import Timebase
from .. import get_root

__t = gettext.translation(
    "messages", localedir=os.path.join(get_root(), "locales"), fallback=True
)
_ = __t.gettext


class CxTime:
    __TC_PATTERN = r"(\d{2}):(\d{2}):(\d{2})[:;.,](\d+)"

    def __init__(self, milliseconds: int):
        self.__milliseconds = int(milliseconds)

    @property
    def total_milliseconds(self):
        return self.__milliseconds

    @property
    def total_seconds(self):
        return self.__milliseconds / 1000.0

    @property
    def total_minutes(self):
        return self.total_seconds / 60.0

    @property
    def total_hours(self):
        return self.total_minutes / 60.0

    @property
    def total_days(self):
        return self.total_hours / 24.0

    @property
    def milliseconds(self):
        return self.__milliseconds % 1000

    @property
    def seconds(self):
        return self.__milliseconds // 1000 % 60

    @property
    def minutes(self):
        return self.__milliseconds // 1000 // 60 % 60

    @property
    def hours(self):
        return self.__milliseconds // 1000 // 60 // 60 % 24

    @property
    def days(self):
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
        parts = []
        if self.days > 0:
            parts.append(f"{self.days}{_("日")}")
        if self.hours > 0:
            parts.append(f"{self.hours}{_("小时")}")
        if self.minutes > 0:
            parts.append(f"{self.minutes}{_("分")}")
        if self.seconds > 0:
            parts.append(f"{self.seconds}{_("秒")}")
        if self.milliseconds > 0 > self.total_minutes:
            parts.append(f"{self.milliseconds}{_("毫秒")}")
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
        return cls(milliseconds)

    @classmethod
    def from_seconds(cls, seconds: float):
        return cls(round(seconds * 1000))

    @classmethod
    def from_minutes(cls, minutes: float):
        return cls(round(minutes * 60 * 1000))

    @classmethod
    def from_hours(cls, hours: float):
        return cls(round(hours * 60 * 60 * 1000))

    @classmethod
    def from_days(cls, days: float):
        return cls(round(days * 24 * 60 * 60 * 1000))

    @classmethod
    def zero(cls):
        return cls(0)

    @classmethod
    def one_second(cls):
        return cls.from_seconds(1)

    def to_timestamp(self) -> str:
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}.{self.milliseconds:03d}"

    def to_timecode(self, timebase: Timebase) -> str:
        sep = ";" if timebase.drop_frame else ":"
        ff = self.milliseconds / 1000.0 * timebase.fps
        ff_digits = len(str(timebase.fps))
        ff_str = f"{round(ff):0{ff_digits}d}"
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}{sep}{ff_str}"

    @classmethod
    def from_timestamp(cls, ts: str):
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
        match = re.match(CxTime.__TC_PATTERN, tc)
        if not match:
            raise ValueError(f"Invalid timecode format: {tc}")
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        frames = int(match.group(4))
        milliseconds = int(round(frames / timebase.fps * 1000))
        return cls(hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds)
