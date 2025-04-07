from numbers import Number
import re
from typing import SupportsInt


class FileSize:
    standard = "binary"  # "binary" or "international"

    @classmethod
    def __unit_factor(cls) -> int:
        return 1024 if cls.standard == "binary" else 1000

    @classmethod
    def __unit_string(cls, unit: str) -> str:
        upper = unit.upper()
        if upper == "B":
            return "B"
        return f"{upper}{"B" if cls.standard == "binary" else "iB"}"

    def __init__(self, bytes: int | float):
        self.__bytes = int(0 if bytes < 0 else bytes)

    @classmethod
    def from_bytes(cls, bytes):
        return cls(bytes)

    @classmethod
    def from_kilobytes(cls, kilobytes):
        return cls(kilobytes * cls.__unit_factor())

    @classmethod
    def from_megabytes(cls, megabytes):
        return cls(megabytes * cls.__unit_factor() ** 2)

    @classmethod
    def from_gigabytes(cls, gigabytes):
        return cls(gigabytes * cls.__unit_factor() ** 3)

    @classmethod
    def from_terabytes(cls, terabytes):
        return cls(terabytes * cls.__unit_factor() ** 4)

    @classmethod
    def from_petabytes(cls, petabytes):
        return cls(petabytes * cls.__unit_factor() ** 5)

    @classmethod
    def from_exabytes(cls, exabytes):
        return cls(exabytes * cls.__unit_factor() ** 6)

    @property
    def total_bytes(self) -> int:
        return self.__bytes

    @property
    def total_kilobytes(self) -> float:
        return self.__bytes / self.__unit_factor()

    @property
    def total_megabytes(self) -> float:
        return self.__bytes / self.__unit_factor() ** 2

    @property
    def total_gigabytes(self) -> float:
        return self.__bytes / self.__unit_factor() ** 3

    @property
    def total_terabytes(self) -> float:
        return self.__bytes / self.__unit_factor() ** 4

    @property
    def total_petabytes(self) -> float:
        return self.__bytes / self.__unit_factor() ** 5

    @property
    def total_exabytes(self) -> float:
        return self.__bytes / self.__unit_factor() ** 6

    @property
    def pretty_string(self) -> str:
        if self.total_exabytes >= 1:
            return f"{self.total_exabytes:.2f} {self.__unit_string('E')}"
        elif self.total_petabytes >= 1:
            return f"{self.total_petabytes:.2f} {self.__unit_string('P')}"
        elif self.total_terabytes >= 1:
            return f"{self.total_terabytes:.2f} {self.__unit_string('T')}"
        elif self.total_gigabytes >= 1:
            return f"{self.total_gigabytes:.2f} {self.__unit_string('G')}"
        elif self.total_megabytes >= 1:
            return f"{self.total_megabytes:.2f} {self.__unit_string('M')}"
        elif self.total_kilobytes >= 1:
            return f"{self.total_kilobytes:.2f} {self.__unit_string('K')}"
        else:
            return f"{self.total_bytes} {self.__unit_string('B')}"

    @classmethod
    def from_string(cls, string: str):
        pattern = re.compile(
            r"(?<number>\d+(\.\d+)?)\s*(?<unit>[kmgtpe])b?", re.IGNORECASE
        )
        match = pattern.match(string)
        if not match:
            raise ValueError(f'Invalid string format: "{string}"')
        number = float(match.group("number"))
        unit = match.group("unit").upper()
        if unit == "K":
            return cls.from_kilobytes(number)
        elif unit == "M":
            return cls.from_megabytes(number)
        elif unit == "G":
            return cls.from_gigabytes(number)
        elif unit == "T":
            return cls.from_terabytes(number)
        elif unit == "P":
            return cls.from_petabytes(number)
        elif unit == "E":
            return cls.from_exabytes(number)
        else:
            return cls.from_bytes(number)

    def __eq__(self, other):
        if other == 0:
            return self.total_bytes == 0
        if not isinstance(other, FileSize):
            raise NotImplementedError("Cannot compare FileSize with other types")
        return self.total_bytes == other.total_bytes

    def __ne__(self, other):
        if other == 0:
            return self.total_bytes != 0
        if not isinstance(other, FileSize):
            raise NotImplementedError("Cannot compare FileSize with other types")
        return self.total_bytes != other.total_bytes

    def __lt__(self, other):
        if not isinstance(other, FileSize):
            raise NotImplementedError("Cannot compare FileSize with other types")
        return self.total_bytes < other.total_bytes

    def __le__(self, other):
        if not isinstance(other, FileSize):
            raise NotImplementedError("Cannot compare FileSize with other types")
        return self.total_bytes <= other.total_bytes

    def __add__(self, other):
        if not isinstance(other, FileSize):
            raise NotImplementedError("Cannot add FileSize with other types")
        return FileSize(self.total_bytes + other.total_bytes)

    def __sub__(self, other):
        if not isinstance(other, FileSize):
            raise NotImplementedError("Cannot subtract FileSize with other types")
        return FileSize(self.total_bytes - other.total_bytes)

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            raise NotImplementedError("Cannot multiply FileSize with other types")
        return FileSize(self.total_bytes * other)

    def __truediv__(self, other):
        if not isinstance(other, (int, float)):
            raise NotImplementedError("Cannot divide FileSize with other types")
        return FileSize(self.total_bytes / other)
