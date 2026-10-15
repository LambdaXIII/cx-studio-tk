"""SubRip（SRT）格式实现。

SubRip 无正式规范，本实现按其事实标准读写：

- 时间行形如 ``HH:MM:SS,mmm --> HH:MM:SS,mmm``，两侧时间由本模块自持的
  TimeCodec 严格解析与渲染，模式不进入任何跨组件接口。
- 每个字幕块由「序号行 + 时间行 + 台词」组成，块间以一个空行分隔；序号行
  仅作字面标记，解析时忽略其内容，且其缺失被容忍。
- 台词可跨多行，原文换行以模型 ``text`` 字段的真实 ``\\n`` 承载。

SRT 序列内部不允许交叠，故写向会按 Item 时序做贪心分组：与当前输出组
最晚终点交叠的 Item 另起一组，每组写成一个文件（多组时以 ``.part<k>``
命名），从而在格式侧消化交叠而不丢片。
"""

from collections.abc import Iterable
from pathlib import Path

from cx_studio.core import CxTime, TimeRange
from cx_studio.filesystem import detect_file_encoding

from ..errors import FormatError
from ..format import Format
from ..loader import SubtitleLoader
from ..model import SubtitleItem
from ..saver import SubtitleSaver
from ..timecodec import TimeCodec

__all__ = ["SrtLoader", "SrtSaver", "SrtFormat"]

_SRT_TIMECODE = TimeCodec("HH:MM:SS,mmm")


class SrtLoader(SubtitleLoader):
    """SRT 读向：把 SubRip 文本解析为 Item 列表。

    读取、编码判定与块解析全部自行完成：按探测到的编码解出文本后，以空行
    切分为字幕块，逐块提取时间范围与台词。解析是忠实的——不重排、不丢弃、
    不改写来源内容；任何结构或时间语法缺陷都以带行号的 FormatError 报出，
    不静默跳过、不部分返回。
    """

    def load(self, path: Path) -> list[SubtitleItem]:
        """从 SRT 文件提取全部 Item。

        以探测编码读入文本并解析为块，按块在来源中的出现顺序产出 Item。

        Args:
            path: SRT 文件路径。

        Returns:
            list[SubtitleItem]: 依来源出现顺序排列的 Item 列表。

        Raises:
            FormatError: 编码无法判定或解码失败，或某块不符合 SubRip 结构。
            OSError: 来源不可读等系统级失败。
        """
        text = self._read_text(path)
        return [self._parse_block(block) for block in self._split_blocks(text)]

    def _read_text(self, path: Path) -> str:
        """按探测编码把来源文件读成文本。

        探测不出编码，或按探测结果解码失败时抛 FormatError，不猜测、不静默
        降级。文本模式读入时统一换行，供后续按行解析。

        Args:
            path: 来源文件路径。

        Returns:
            str: 解码后的文件全文。

        Raises:
            FormatError: 探测返回 None，或编码名无效/解码失败。
            OSError: 来源不可读等系统级失败。
        """
        encoding = detect_file_encoding(path)
        if encoding is None:
            raise FormatError(f"无法判定 SRT 来源的字符编码：{path}")
        try:
            with path.open("r", encoding=encoding) as stream:
                return stream.read()
        except (UnicodeDecodeError, LookupError) as error:
            raise FormatError(f"SRT 来源解码失败（{encoding}）：{error}") from error

    def _split_blocks(self, text: str) -> list[list[tuple[int, str]]]:
        """把全文按空行切分为字幕块，并保留每行的来源行号。

        空行是块分隔符：一个非空行序列构成一块。文件首部出现空行，或连续
        空行之间夹出的空块（纯空白）都视为结构错误，带行号报出；文件末尾
        的单个空行不构成块，予以容忍。

        Args:
            text: 文件全文。

        Returns:
            list[list[tuple[int, str]]]: 每块为 ``(行号, 行文本)`` 的序列，
                行号从 1 起、与来源一致。

        Raises:
            FormatError: 出现空块（纯空白）。
        """
        blocks: list[list[tuple[int, str]]] = []
        current: list[tuple[int, str]] = []
        for number, line in enumerate(text.splitlines(), start=1):
            if line.strip() == "":
                if not current:
                    raise FormatError("空的字幕块（纯空白）", line=number)
                blocks.append(current)
                current = []
            else:
                current.append((number, line))
        if current:
            blocks.append(current)
        return blocks

    def _parse_block(self, block: list[tuple[int, str]]) -> SubtitleItem:
        """解析单个字幕块为 Item。

        块内首个非空行若为纯数字则视为序号行并忽略；其后一行必须是时间行，
        其余行以换行拼成台词原文。序号行缺失被容忍，时间行缺失或语法错误
        按行号报错。

        Args:
            block: 块内各行，元素为 ``(行号, 行文本)``。

        Returns:
            SubtitleItem: 该块对应的条目（无说话人、无扩展位）。

        Raises:
            FormatError: 块缺少时间行，或时间行语法错误。
        """
        position = 0
        if block[0][1].strip().isdigit():
            position = 1
        if position >= len(block):
            raise FormatError("字幕块缺少时间行", line=block[0][0])

        time_number, time_text = block[position]
        time_range = self._parse_time_line(time_text, time_number)
        body = "\n".join(line for _, line in block[position + 1 :])
        return SubtitleItem(time_range=time_range, text=body)

    def _parse_time_line(self, text: str, number: int) -> TimeRange:
        """解析字幕块的 ``start --> end`` 时间行。

        以 ``-->`` 一分为二，两侧各自交 TimeCodec 全串严格解析；分隔符缺失、
        数量异常或任一侧语法不符都以本行行号抛 FormatError。

        Args:
            text: 时间行原文。
            number: 该行在来源中的行号。

        Returns:
            TimeRange: 由起止时刻构成的区间。

        Raises:
            FormatError: 时间行缺少 ``-->`` 或时间文本不符合模式。
        """
        parts = text.split("-->")
        if len(parts) != 2:
            raise FormatError("时间行格式错误：应形如 'start --> end'", line=number)
        raw_start, raw_end = (part.strip() for part in parts)
        try:
            start = _SRT_TIMECODE.parse(raw_start)
            end = _SRT_TIMECODE.parse(raw_end)
        except FormatError as error:
            raise FormatError(error.message, line=number) from error
        return TimeRange(start, end - start)


class SrtSaver(SubtitleSaver):
    """SRT 写向：把 Item 集合组织为一个或多个 SubRip 文件。

    SRT 序列内部不允许交叠，故写向按 Item 时序做贪心分组：顺序扫描，与
    当前组最晚终点交叠的 Item 另起一组，组数不求最优但每组内部不交叠、
    全部 Item 无丢失。单组直接写目标路径，多组则每组写成一个 ``.part<k>``
    文件（k 从 1 起、按组首起点升序）。每文件内按 Item 时序从 1 重新编号，
    多行台词原样多行写出，UTF-8 无 BOM 写盘。
    """

    def save(self, items: Iterable[SubtitleItem], target: Path) -> list[Path]:
        """把 Item 集合写出为 SRT 文件。

        先一次性预检全部目标路径（含派生的 ``.part<k>``）：任一已存在即中止，
        不写出、不覆盖；随后逐组写盘，并返回实际产出的路径列表。

        Args:
            items: 待写出的 Item 可迭代序列。
            target: 目标文件路径；多文件输出以它为命名基准。

        Returns:
            list[Path]: 实际写出的文件路径列表，顺序与写入顺序一致。

        Raises:
            FormatError: 任一目标路径已存在；或台词含空行等无法以 SubRip
                块结构表达的入参内容。
            OSError: 目标目录不可写等系统级失败。
        """
        groups = self._group(items)
        paths = self._resolve_paths(target, len(groups))
        self._preflight(paths)
        self._validate(groups)
        for path, group in zip(paths, groups):
            self._write(path, group)
        return paths

    def _group(self, items: Iterable[SubtitleItem]) -> list[list[SubtitleItem]]:
        """把 Item 集合贪心分组为内部不交叠的输出组。

        Item 先按起点稳定排序，再顺序扫描：新 Item 与当前组最晚终点交叠
        （即与当前组区间 ``is_overlapped_with``）时另起一组，否则并入当前组。
        贪心不保证组数最少，但保证每组内部不交叠。空输入产出一个空组，使
        写向仍落到目标路径。

        Args:
            items: 待分组的 Item 可迭代序列。

        Returns:
            list[list[SubtitleItem]]: 按组首起点升序排列的分组。
        """
        ordered = sorted(items, key=lambda item: item.start)
        groups: list[list[SubtitleItem]] = []
        ends: list[CxTime] = []
        for item in ordered:
            if groups:
                latest_end = ends[-1]
                span = TimeRange(groups[-1][0].start, latest_end - groups[-1][0].start)
                if item.time_range.is_overlapped_with(span):
                    groups.append([item])
                    ends.append(item.time_range.end)
                    continue
                groups[-1].append(item)
                if item.time_range.end > latest_end:
                    ends[-1] = item.time_range.end
                continue
            groups.append([item])
            ends.append(item.time_range.end)
        if not groups:
            groups.append([])
        return groups

    def _resolve_paths(self, target: Path, count: int) -> list[Path]:
        """按组数解析出全部目标路径。

        单组时目标即 ``target`` 本身；多组时以目标 stem 加 ``.part<k>``、
        扩展名与目录跟随目标路径。

        Args:
            target: 目标文件路径。
            count: 输出组数。

        Returns:
            list[Path]: 与组分一一对应的路径列表。
        """
        if count <= 1:
            return [target]
        return [
            target.parent / f"{target.stem}.part{index}{target.suffix}"
            for index in range(1, count + 1)
        ]

    def _preflight(self, paths: list[Path]) -> None:
        """写前一次性预检全部目标路径。

        Args:
            paths: 即将写出的全部文件路径。

        Raises:
            FormatError: 任一路径已存在；此时不写出任何文件、不覆盖既有文件。
        """
        for path in paths:
            if path.exists():
                raise FormatError(f"目标文件已存在，拒绝覆盖：{path}")

    def _validate(self, groups: list[list[SubtitleItem]]) -> None:
        """写前校验全部台词的 SubRip 可表达性。

        SubRip 以空行分隔字幕块，故台词内的空行（或首尾换行）会破坏块结构、
        使写出物无法被本 Loader 回读；此类内容在此一次性拒绝，避免写出残缺
        或不可解析的文件。

        Args:
            groups: 待写出的全部输出组。

        Raises:
            FormatError: 任一台词含空行或首尾换行。
        """
        for group in groups:
            for item in group:
                if item.text and any(
                    line.strip() == "" for line in item.text.split("\n")
                ):
                    raise FormatError("台词含空行或首尾换行，无法以 SubRip 块表达")

    def _write(self, path: Path, group: list[SubtitleItem]) -> None:
        """把一组 Item 以 SubRip 结构写入单个文件。

        组内按 Item 时序从 1 重新编号，时间经 TimeCodec 取整到模式精度后
        渲染，多行台词原样多行写出，块间以空行分隔，UTF-8 无 BOM 写盘。

        Args:
            path: 目标文件路径。
            group: 本组内按时序排列的 Item。
        """
        chunks: list[str] = []
        for number, item in enumerate(group, start=1):
            start = _SRT_TIMECODE.format(_SRT_TIMECODE.round_to_unit(item.start))
            end = _SRT_TIMECODE.format(_SRT_TIMECODE.round_to_unit(item.time_range.end))
            chunk = f"{number}\n{start} --> {end}"
            if item.text:
                chunk = f"{chunk}\n{item.text}"
            chunks.append(chunk)
        content = "\n\n".join(chunks)
        if content:
            content += "\n"
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)


SrtFormat = Format(
    name="srt",
    extensions=(".srt",),
    loader=SrtLoader(),
    saver=SrtSaver(),
)
