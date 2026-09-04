"""文件大小值对象（FileSize）：字节数与两套单位制的换算、格式化与解析。

内部以整数字节为唯一数值存储，支持 binary（1024 进制）与
international（1000 进制）两套单位制，提供 from_* 系列构造、
total_* 系列换算、pretty_string 人类可读输出与字符串解析。
"""

import re
from typing import Literal


class FileSize:
    """以整数字节数为唯一数值状态的文件大小值对象。

    数值与单位语义：
        - 内部只保存 ``total_bytes``（int）：构造时负值按 0 处理，
          浮点数向零取整（``int(0 if bytes < 0 else bytes)``）。
        - ``standard``（类属性 ``Standard`` 的类型别名取值
          ``"binary"``/``"international"``）同时决定换算进制与单位后缀：
            - ``"binary"``：进制 1024，后缀 B/KB/MB/GB/TB/PB/EB；
            - ``"international"``：进制 1000，后缀 B/KiB/MiB/GiB/TiB/PiB/EiB
              （注意：本类中带 ``i`` 的标签属于 international 制，与常见
              “KiB=1024”的命名习惯相反，以代码为准）。
        - 比较：``==``/``!=`` 先特判与整数 ``0`` 的比较（视作零字节量），
          与另一个 FileSize 比较时按 total_bytes 比较；``<``/``<=`` 仅
          接受 FileSize 且无 0 特判；其它类型一律抛出
          ``NotImplementedError``。
        - 算术：``+``/``-`` 要求两个 FileSize；``*``/``/`` 接受 int/float；
          结果一律是以默认 ``"binary"`` 单位制重建的新 FileSize
          （不继承操作数的 standard）。
        - ``pretty_string``：自大到小依次检查 EB/PB/TB/GB/MB/KB，输出首个
          换算值 ≥ 1 的单位（两位小数）；全部不足 1 时输出整数字节数。
        - ``from_string`` 的可解析文本格式见该方法 docstring。
    """

    Standard = Literal["binary", "international"]

    @staticmethod
    def __unit_factor(standard: Standard) -> int:
        return 1024 if standard == "binary" else 1000

    def __unit_string(self, unit: str) -> str:
        upper = unit.upper()
        if upper == "B":
            return "B"
        return f"{upper}{'B' if self.__standard == 'binary' else 'iB'}"

    def __init__(
        self,
        bytes: int | float,
        standard: Standard = "binary",
    ):
        self.__bytes = int(0 if bytes < 0 else bytes)
        self.__standard: FileSize.Standard = standard

    @classmethod
    def from_bytes(cls, bytes, standard: Standard = "binary"):
        """从字节数构造实例。

        Args:
            bytes: 字节数；负数按 0 处理、小数向零取整。
            standard: 换算进制所属单位制，默认 ``"binary"``。

        Returns:
            FileSize: 以给定字节数与单位制构造的实例。
        """
        return cls(bytes, standard)

    @classmethod
    def from_kilobytes(cls, kilobytes, standard: Standard = "binary"):
        """从千字节数构造实例（字节 = 千字节 × 进制¹）。

        Args:
            kilobytes: 以千字节为单位的数量（可为小数）。
            standard: 换算进制所属单位制，默认 ``"binary"``。

        Returns:
            FileSize: 换算为字节后构造的实例。
        """
        return cls(kilobytes * cls.__unit_factor(standard), standard)

    @classmethod
    def from_megabytes(cls, megabytes, standard: Standard = "binary"):
        """从兆字节数构造实例（字节 = 兆字节 × 进制²）。

        Args:
            megabytes: 以兆字节为单位的数量（可为小数）。
            standard: 换算进制所属单位制，默认 ``"binary"``。

        Returns:
            FileSize: 换算为字节后构造的实例。
        """
        return cls(megabytes * cls.__unit_factor(standard) ** 2, standard)

    @classmethod
    def from_gigabytes(cls, gigabytes, standard: Standard = "binary"):
        """从吉字节数构造实例（字节 = 吉字节 × 进制³）。

        Args:
            gigabytes: 以吉字节为单位的数量（可为小数）。
            standard: 换算进制所属单位制，默认 ``"binary"``。

        Returns:
            FileSize: 换算为字节后构造的实例。
        """
        return cls(gigabytes * cls.__unit_factor(standard) ** 3, standard)

    @classmethod
    def from_terabytes(cls, terabytes, standard: Standard = "binary"):
        """从太字节数构造实例（字节 = 太字节 × 进制⁴）。

        Args:
            terabytes: 以太字节为单位的数量（可为小数）。
            standard: 换算进制所属单位制，默认 ``"binary"``。

        Returns:
            FileSize: 换算为字节后构造的实例。
        """
        return cls(terabytes * cls.__unit_factor(standard) ** 4, standard)

    @classmethod
    def from_petabytes(cls, petabytes, standard: Standard = "binary"):
        """从拍字节数构造实例（字节 = 拍字节 × 进制⁵）。

        Args:
            petabytes: 以拍字节为单位的数量（可为小数）。
            standard: 换算进制所属单位制，默认 ``"binary"``。

        Returns:
            FileSize: 换算为字节后构造的实例。
        """
        return cls(petabytes * cls.__unit_factor(standard) ** 5, standard)

    @classmethod
    def from_exabytes(cls, exabytes, standard: Standard = "binary"):
        """从艾字节数构造实例（字节 = 艾字节 × 进制⁶）。

        Args:
            exabytes: 以艾字节为单位的数量（可为小数）。
            standard: 换算进制所属单位制，默认 ``"binary"``。

        Returns:
            FileSize: 换算为字节后构造的实例。
        """
        return cls(exabytes * cls.__unit_factor(standard) ** 6, standard)

    @property
    def standard(self) -> str:
        """当前使用的单位制。

        Returns:
            str: ``"binary"``（1024 进制）或 ``"international"``（1000 进制）。
        """
        return self.__standard

    @property
    def total_bytes(self) -> int:
        """字节总数（内部唯一数值状态）。

        Returns:
            int: 构造时归一后的整数字节数，恒为非负。
        """
        return self.__bytes

    @property
    def total_kilobytes(self) -> float:
        """按当前单位制换算的千字节数。

        Returns:
            float: total_bytes ÷ 进制（1024 或 1000）。
        """
        return self.__bytes / self.__unit_factor(self.__standard)

    @property
    def total_megabytes(self) -> float:
        """按当前单位制换算的兆字节数。

        Returns:
            float: total_bytes ÷ 进制²。
        """
        return self.__bytes / self.__unit_factor(self.__standard) ** 2

    @property
    def total_gigabytes(self) -> float:
        """按当前单位制换算的吉字节数。

        Returns:
            float: total_bytes ÷ 进制³。
        """
        return self.__bytes / self.__unit_factor(self.__standard) ** 3

    @property
    def total_terabytes(self) -> float:
        """按当前单位制换算的太字节数。

        Returns:
            float: total_bytes ÷ 进制⁴。
        """
        return self.__bytes / self.__unit_factor(self.__standard) ** 4

    @property
    def total_petabytes(self) -> float:
        """按当前单位制换算的拍字节数。

        Returns:
            float: total_bytes ÷ 进制⁵。
        """
        return self.__bytes / self.__unit_factor(self.__standard) ** 5

    @property
    def total_exabytes(self) -> float:
        """按当前单位制换算的艾字节数。

        Returns:
            float: total_bytes ÷ 进制⁶。
        """
        return self.__bytes / self.__unit_factor(self.__standard) ** 6

    @property
    def pretty_string(self) -> str:
        """格式化为人类可读的大小字符串（保留两位小数）。

        自大到小（EB→PB→TB→GB→MB→KB）选择首个换算值 ≥ 1 的单位并以
        ``数值 + 单位标签`` 输出（如 ``1.50 GB``）；所有单位换算值均不足
        1 时输出整数字节数加 ``B``。标签随 standard 取 binary 系或
        international 系（见类 docstring）。

        Returns:
            str: 格式化后的文本，如 ``1.50 GB``。
        """
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
        """从字符串解析文件大小（固定按默认 binary 单位制构造）。

        解析规则（正则
        ``(?P<number>\\d+\\.?\\d*)\\s*(?P<unit>[kmgtpebits]+)?``，
        不区分大小写，search 语义）：
            - 在文本中搜索“数字（整数部分必须有、小数部分可选）＋可选
              空白＋可选单位字母串”，取首个匹配；
            - 单位字母取自 ``k m g t p e b i t s``，可任意组合、以首字母
              判定量级：K/M/G/T/P/E 分别对应 kilo/mega/giga/tera/peta/exa，
              其余（含 B、bit）一律按字节处理；
            - 单位仅决定换算目标（from_kilobytes…from_exabytes/from_bytes），
              进制固定为 binary（1024）；
            - 文本中找不到数字时抛 ValueError；另注意单位字母虽被正则允许
              省略，但省略时会对 None 调用 upper() 而抛 AttributeError。

        Args:
            string: 形如 ``"1.5 GB"`` / ``"512MB"`` 的文件大小文本。

        Returns:
            FileSize: 解析得到的实例。

        Raises:
            ValueError: 文本中不包含可解析的数字时。
        """
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
