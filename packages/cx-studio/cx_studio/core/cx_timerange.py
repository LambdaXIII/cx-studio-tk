"""时间区间抽象契约（ITimeRange）与实现（TimeRange）。

区间由起止时刻与时长（均为 CxTime）描述，提供重叠/包含判定与
时刻包含判定；TimeRange 以 start + duration 存储，end 为计算属性。
"""

from abc import ABC, abstractmethod

from .cx_time import CxTime


class ITimeRange(ABC):
    """时间区间抽象接口（契约）。

    子类必须提供 start/end/duration 三个只读属性（均为 CxTime），
    其余方法基于这三个属性与 CxTime 的比较运算实现，无需再覆写：

        - ``is_overlapped_with(other)``：两区间是否相交（含端点相触），
          即 ``start <= other.end and end >= other.start``；
        - ``is_contained_by(other)``：本区间是否完全落在 other 内
          （含端点重合），即 ``start >= other.start and end <= other.end``；
        - ``contains_time(time)``：某时刻是否落在本区间内（闭区间），
          即 ``start <= time <= end``。
    """

    @property
    @abstractmethod
    def start(self) -> CxTime:
        """返回区间起点（抽象属性，由子类实现）。

        Returns:
            CxTime: 区间起点时刻。
        """
        pass

    @property
    @abstractmethod
    def end(self) -> CxTime:
        """返回区间终点（抽象属性，由子类实现）。

        Returns:
            CxTime: 区间终点时刻。
        """
        pass

    @property
    @abstractmethod
    def duration(self) -> CxTime:
        """返回区间时长（抽象属性，由子类实现）。

        Returns:
            CxTime: 区间持续时长。
        """
        pass

    def is_overlapped_with(self, other: "ITimeRange") -> bool:
        """判断本区间与另一区间是否有重叠。

        两端点相触（一个区间的终点恰为另一个区间的起点）也视为重叠。

        Args:
            other: 待比较的另一时间区间。

        Returns:
            bool: 有重叠返回 True，否则 False。
        """
        return self.start <= other.end and self.end >= other.start

    def is_contained_by(self, other: "ITimeRange") -> bool:
        """判断本区间是否完全包含于另一区间。

        Args:
            other: 作为容器的另一时间区间。

        Returns:
            bool: 本区间整体落在 other 内（含端点重合）返回 True。
        """
        return self.start >= other.start and self.end <= other.end

    def contains_time(self, time: CxTime) -> bool:
        """判断某时刻是否落在本区间内。

        闭区间语义：时刻等于起点或终点时也视为包含。

        Args:
            time: 待判定的时刻。

        Returns:
            bool: 时刻在 [start, end] 内返回 True。
        """
        return self.start <= time <= self.end


class TimeRange(ITimeRange):
    """基于 ``start + duration`` 存储的时间区间实现。

    内部只保存 start 与 duration 两个 CxTime，end 是按需计算的
    只读派生属性（``start + duration``），三者关系恒为
    ``end == start + duration``。

    赋值语义：
        - 直接写 ``start``/``duration`` 会替换对应的内部值；
        - 写 ``end`` 不会保存终点，而是反向推导时长并更新 duration
          （``duration = end - start``），从而维持上述恒等关系。
    """

    def __init__(self, start: CxTime, duration: CxTime):
        self.__start = start
        self.__duration = duration

    @property
    def start(self) -> CxTime:
        """返回区间起点。

        Returns:
            CxTime: 起点时刻。
        """
        return self.__start

    @property
    def duration(self) -> CxTime:
        """返回区间时长。

        Returns:
            CxTime: 持续时长。
        """
        return self.__duration

    @property
    def end(self) -> CxTime:
        """返回区间终点（派生属性，等于 start + duration）。

        Returns:
            CxTime: 终点时刻。
        """
        return self.start + self.duration

    @start.setter
    def start(self, start: CxTime):
        self.__start = start

    @duration.setter
    def duration(self, duration: CxTime):
        self.__duration = duration

    @end.setter
    def end(self, end: CxTime):
        self.__duration = end - self.start

    def __eq__(self, other: object) -> bool:
        """同类型且起止时间相等视为相等。对非 ITimeRange 类型返回 NotImplemented。"""
        if not isinstance(other, ITimeRange):
            return NotImplemented
        return self.start == other.start and self.duration == other.duration

    def __ne__(self, other: object) -> bool:
        """__eq__ 的逆。对非 ITimeRange 类型返回 NotImplemented。"""
        if not isinstance(other, ITimeRange):
            return NotImplemented
        return self.start != other.start or self.duration != other.duration
