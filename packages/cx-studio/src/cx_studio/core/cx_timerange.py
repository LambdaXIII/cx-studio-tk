from abc import ABC, abstractmethod

from .cx_time import CxTime


class ITimeRange(ABC):

    @property
    @abstractmethod
    def start(self) -> CxTime:
        pass

    @property
    @abstractmethod
    def end(self) -> CxTime:
        pass

    @property
    @abstractmethod
    def duration(self) -> CxTime:
        pass

    def is_overlapped_with(self, other: "ITimeRange") -> bool:
        return self.start <= other.end and self.end >= other.start

    def is_contained_by(self, other: "ITimeRange") -> bool:
        return self.start >= other.start and self.end <= other.end

    def contains_time(self, time: CxTime) -> bool:
        return self.start <= time <= self.end


class TimeRange(ITimeRange):
    def __init__(self, start: CxTime, duration: CxTime):
        self.__start = start
        self.__duration = duration

    @property
    def start(self) -> CxTime:
        return self.__start

    @property
    def duration(self) -> CxTime:
        return self.__start + self.__duration

    @property
    def end(self) -> CxTime:
        return self.duration - self.start

    @start.setter
    def start(self, start: CxTime):
        self.__start = start

    @duration.setter
    def duration(self, duration: CxTime):
        self.__duration = duration

    @end.setter
    def end(self, end: CxTime):
        self.__duration = end - self.start

    def __eq__(self, other: "ITimeRange") -> bool:
        return self.start == other.start and self.duration == other.duration

    def __ne__(self, other: "ITimeRange") -> bool:
        return self.start != other.start or self.duration != other.duration
