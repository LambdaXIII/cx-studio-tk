"""CSV 字幕格式：RFC 4180 语法与本工具自定表头契约。

字幕 CSV 没有通用标准，故本实现自定表头契约：保留列为 ``start``、``end``、
``text``、``speaker``，必须按此顺序位于表头最前；其后的列都是扩展列，列名
即 Item 扩展位的键、单元格即其值，原样互映射——不加前缀也不去前缀，故只
适合与本实现往返，或与同样遵守本契约的来源互转。

引号规则（含引号内换行，即多行台词）由标准库 ``csv`` 按 RFC 4180 承载，
本模块不手写解析。时间列是毫秒精度的 ``HH:MM:SS.mmm``，格式实现内部的常量，
对外不暴露。

表头不符、时间语法错、扩展键与保留列同名都抛 FormatError，不做宽松兜底。
"""

import csv
import io
from collections.abc import Iterable
from pathlib import Path

from cx_studio.core import TimeRange
from cx_studio.filesystem import detect_file_encoding

from ..errors import FormatError
from ..format import Format
from ..loader import SubtitleLoader
from ..model import SubtitleItem
from ..saver import SubtitleSaver
from ..timecodec import TimeCodec

__all__ = ["CsvLoader", "CsvSaver", "CsvFormat", "RESERVED_COLUMNS"]

RESERVED_COLUMNS: tuple[str, ...] = ("start", "end", "text", "speaker")
"""CSV 表头的保留列，必须依序出现在表头最前。

这是本实现的自定契约：字幕 CSV 无通用标准，保留列之外的列一律视为扩展列，
列名即 Item 扩展位的键。
"""

_TIME_PATTERN = "HH:MM:SS.mmm"
"""CSV 的时间表示模式，本格式实现内部的常量。"""


class CsvLoader(SubtitleLoader):
    """CSV 读向：按自定表头契约从单文件提取 Item。

    表头契约：首个非空行即表头，最前的四列必须依序为 ``start``、``end``、
    ``text``、``speaker``；其余列为扩展列，列名即扩展位的键。数据行按来源
    顺序原样产出，不重排、不丢弃、不改写，交叠与乱序照实保留。

    单元格语义：``start``/``end`` 是严格匹配 ``HH:MM:SS.mmm`` 的时间文本；
    ``text`` 原样保留（RFC 4180 引号内的换行即多行台词）；``speaker`` 为空
    单元格时记 None，否则原样；扩展列空单元格表示该键不存在，非空时以列名
    为键写入扩展位。

    表头不合法、数据行列数与表头不符、时间文本不合法都抛 FormatError 并尽量
    带行号；空白行（连一个非空单元格都没有）跳过，不产出 Item。
    """

    def __init__(self) -> None:
        """编译时间模式，构造可复用的读向实现。"""
        self._codec = TimeCodec(_TIME_PATTERN)

    def load(self, path: Path) -> list[SubtitleItem]:
        """从单个 CSV 文件提取全部 Item。

        编码沿用共享探测：``detect_file_encoding`` 判不出结论即报错，不做
        回退猜测。

        Args:
            path: CSV 来源文件路径。

        Returns:
            list[SubtitleItem]: 依来源行序排列的 Item 列表；只有表头时为空列表。

        Raises:
            FormatError: 编码无法判定或解码失败、表头不符、行列数不符、时间
                文本不合法。
            OSError: 来源不可读等系统级失败。
        """
        encoding = detect_file_encoding(path)
        if encoding is None:
            raise FormatError(f"无法判定 CSV 来源的字符编码：{path}")
        try:
            text = path.read_bytes().decode(encoding)
        except (UnicodeDecodeError, LookupError) as exc:
            raise FormatError(f"CSV 来源解码失败（{encoding}）：{exc}") from exc

        reader = csv.reader(io.StringIO(text, newline=""))
        header: list[str] | None = None
        items: list[SubtitleItem] = []
        for row in reader:
            if not row or not any(row):
                continue
            if header is None:
                header = self._parse_header(row)
                continue
            items.append(self._parse_data_row(row, header, reader.line_num))

        if header is None:
            raise FormatError("CSV 来源缺少表头", line=1)
        return items

    def _parse_header(self, row: list[str]) -> list[str]:
        """校验表头并返回之；不合法时抛 FormatError（行号 1）。

        Args:
            row: 首个非空行解析出的单元格列表。

        Returns:
            list[str]: 校验通过的表头列名（含保留列）。

        Raises:
            FormatError: 保留列缺失/错序，或扩展列名为空、与保留列同名、重复。
        """
        if row[: len(RESERVED_COLUMNS)] != list(RESERVED_COLUMNS):
            expected = ",".join(RESERVED_COLUMNS)
            raise FormatError(f"CSV 表头必须以 {expected} 四列依序开头", line=1)

        seen = set(RESERVED_COLUMNS)
        for name in row[len(RESERVED_COLUMNS) :]:
            if name == "":
                raise FormatError("CSV 扩展列名不得为空", line=1)
            if name in seen:
                raise FormatError(f"CSV 扩展列名重复或撞保留列：{name!r}", line=1)
            seen.add(name)
        return row

    def _parse_data_row(
        self, row: list[str], header: list[str], line: int
    ) -> SubtitleItem:
        """把一行数据解析为 Item；不合法时抛 FormatError（带行号）。

        Args:
            row: 数据行解析出的单元格列表（已排除空白行）。
            header: 已校验的表头列名。
            line: 该行在来源中的物理行号（csv.reader 的 line_num）。

        Returns:
            SubtitleItem: 解析得到的条目。

        Raises:
            FormatError: 列数与表头不符，或时间列不合法。
        """
        if len(row) != len(header):
            raise FormatError(
                f"数据行列数 {len(row)} 与表头列数 {len(header)} 不符", line=line
            )

        try:
            start = self._codec.parse(row[0])
            end = self._codec.parse(row[1])
        except FormatError as exc:
            raise FormatError(f"时间列解析失败：{exc.message}", line=line) from exc

        extra = {
            name: row[index]
            for index, name in enumerate(
                header[len(RESERVED_COLUMNS) :], start=len(RESERVED_COLUMNS)
            )
            if row[index] != ""
        }
        return SubtitleItem(
            time_range=TimeRange(start=start, duration=end - start),
            text=row[2],
            speaker=row[3] if row[3] != "" else None,
            extra=extra,
        )


class CsvSaver(SubtitleSaver):
    """CSV 写向：把 Item 集合写为单个 CSV 文件。

    输出单文件，交叠照收（CSV 表头不含编号，交叠无需拆分）。写出前按
    ``start`` 稳定排序；扩展列集合取各 Item 扩展键的并集，按键名排序输出以
    保证确定性；扩展键与保留列同名时抛错，防止表头语义被挤占。

    单元格语义与读向互逆：``speaker`` 为 None 写空单元格；扩展列缺键写空
    单元格；``text`` 中的换行由 RFC 4180 引号承载。行终止符固定 ``\\r\\n``，
    编码 UTF-8 且不带 BOM，因此读向可无损还原。
    """

    def __init__(self) -> None:
        """编译时间模式，构造可复用的写向实现。"""
        self._codec = TimeCodec(_TIME_PATTERN)

    def save(self, items: Iterable[SubtitleItem], target: Path) -> list[Path]:
        """把 Item 集合写出到目标路径的单个 CSV 文件。

        Args:
            items: 待写出的 Item 可迭代序列，按 ``start`` 稳定排序后写出。
            target: 目标文件路径。

        Returns:
            list[Path]: 实际写出的文件路径列表，恒为 ``[target]``。

        Raises:
            FormatError: 任一 Item 的扩展键与保留列同名，或目标文件已存在
                （此时不写出任何文件、不覆盖既有文件）。
            OSError: 目标目录不可写等系统级失败。
        """
        ordered = sorted(items, key=lambda item: item.start)
        extra_keys = sorted({key for item in ordered for key in item.extra})

        collisions = [key for key in extra_keys if key in RESERVED_COLUMNS]
        if collisions:
            raise FormatError(
                "扩展键与保留列同名，无法写出：" + ", ".join(map(repr, collisions))
            )
        if target.exists():
            raise FormatError(f"目标文件已存在，拒绝覆盖：{target}")

        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\r\n")
            writer.writerow([*RESERVED_COLUMNS, *extra_keys])
            for item in ordered:
                row = [
                    self._codec.format(self._codec.round_to_unit(item.start)),
                    self._codec.format(self._codec.round_to_unit(item.time_range.end)),
                    item.text,
                    "" if item.speaker is None else item.speaker,
                ]
                row.extend(item.extra.get(key, "") for key in extra_keys)
                writer.writerow(row)

        return [target]


CsvFormat = Format(
    name="csv",
    extensions=(".csv",),
    loader=CsvLoader(),
    saver=CsvSaver(),
)
