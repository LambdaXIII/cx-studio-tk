class CxTime:

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
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot compare Time with other types")
        return self.total_milliseconds == other.total_milliseconds

    def __ne__(self, other):
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot compare Time with other types")
        return self.total_milliseconds != other.total_milliseconds

    def __lt__(self, other):
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot compare Time with other types")
        return self.total_milliseconds < other.total_milliseconds

    def __le__(self, other):
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
            parts.append(f"{self.days}日")
        if self.hours > 0:
            parts.append(f"{self.hours}小时")
        if self.minutes > 0:
            parts.append(f"{self.minutes}分")
        if self.seconds > 0:
            parts.append(f"{self.seconds}秒")
        if self.milliseconds > 0 and self.total_minutes < 0:
            parts.append(f"{self.milliseconds}毫秒")

    def __add__(self, other):
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot add Time with other types")
        return CxTime(self.total_milliseconds + other.total_milliseconds)

    def __sub__(self, other):
        if not isinstance(other, CxTime):
            raise NotImplementedError("Cannot subtract Time with other types")
        return CxTime(self.total_milliseconds - other.total_milliseconds)
