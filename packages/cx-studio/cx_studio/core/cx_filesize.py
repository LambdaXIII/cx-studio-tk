from ast import TypeAlias
from numbers import Number
import re
from typing import Literal, SupportsInt
import enum


class FileSize:
    Standard = Literal["binary", "international"]

    @staticmethod
    def __unit_factor(standard: Standard) -> int:
        return 1024 if standard == "binary" else 1000

    def __unit_string(self, unit: str) -> str:
        upper = unit.upper()
        if upper == "B":
            return "B"
        return f"{upper}{"B" if self.__standard == "binary" else "iB"}"

    def __init__(
        self,
        bytes: int | float,
        standard: Standard = "binary",
    ):
        self.__bytes = int(0 if bytes < 0 else bytes)
        self.__standard: FileSize.Standard = standard

    @classmethod
    def from_bytes(cls, bytes, standard: Standard = "binary"):
        return cls(bytes, standard)

    @classmethod
    def from_kilobytes(cls, kilobytes, standard: Standard = "binary"):
        return cls(kilobytes * cls.__unit_factor(standard), standard)

    @classmethod
    def from_megabytes(cls, megabytes, standard: Standard = "binary"):
        return cls(megabytes * cls.__unit_factor(standard) ** 2, standard)

    @classmethod
    def from_gigabytes(cls, gigabytes, standard: Standard = "binary"):
        return cls(gigabytes * cls.__unit_factor(standard) ** 3, standard)

    @classmethod
    def from_terabytes(cls, terabytes, standard: Standard = "binary"):
        return cls(terabytes * cls.__unit_factor(standard) ** 4, standard)

    @classmethod
    def from_petabytes(cls, petabytes, standard: Standard = "binary"):
        return cls(petabytes * cls.__unit_factor(standard) ** 5, standard)

    @classmethod
    def from_exabytes(cls, exabytes, standard: Standard = "binary"):
        return cls(exabytes * cls.__unit_factor(standard) ** 6, standard)

    @property
    def standard(self) -> str:
        return self.__standard

    @property
    def total_bytes(self) -> int:
        return self.__bytes

    @property
    def total_kilobytes(self) -> float:
        return self.__bytes / self.__unit_factor(self.__standard)

    @property
    def total_megabytes(self) -> float:
        return self.__bytes / self.__unit_factor(self.__standard) ** 2

    @property
    def total_gigabytes(self) -> float:
        return self.__bytes / self.__unit_factor(self.__standard) ** 3

    @property
    def total_terabytes(self) -> float:
        return self.__bytes / self.__unit_factor(self.__standard) ** 4

    @property
    def total_petabytes(self) -> float:
        return self.__bytes / self.__unit_factor(self.__standard) ** 5

    @property
    def total_exabytes(self) -> float:
        return self.__bytes / self.__unit_factor(self.__standard) ** 6

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
            r"(?P<number>\d+\.?\d*)\s*(?P<unit>[kmgtpebits]+)?", re.IGNORECASE
        )
        match = pattern.search(string)
        if not match:
            raise ValueError(f'Invalid string format: "{string}".')
        number = float(match.group("number"))
        unit = match.group("unit").upper()
        if unit.startswith("K"):
            return cls.from_kilobytes(number)
        elif unit.startswith("M"):
            return cls.from_megabytes(number)
        elif unit.startswith("G"):
            return cls.from_gigabytes(number)
        elif unit.startswith("T"):
            return cls.from_terabytes(number)
        elif unit.startswith("P"):
            return cls.from_petabytes(number)
        elif unit.startswith("E"):
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

    def __replace__(self, /, **changes):
        # supports python 3.13+
        bytes = changes.get("bytes", self.__bytes)
        standard = changes.get("standard", self.__standard)
        return FileSize(bytes, standard)

    def __rich__(self):
        return self.pretty_string
