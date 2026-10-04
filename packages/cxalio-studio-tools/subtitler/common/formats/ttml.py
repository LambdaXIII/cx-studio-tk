"""TTML 字幕格式适配器（W3C TTML 文本子集）。

以标准库 ``xml.etree.ElementTree`` 读写 TTML 的文本子集：``<tt><body><div><p>``
结构、clock 时间字面量与带单位偏移字面量（``10s``、``1.5s``、``100ms``），
换行以 ``<br/>`` 表达。超出子集的结构不建模——复杂 TTML 降级保留时间与文本，
``<p>`` 上的其余属性原样收入条目的扩展位，既不猜测其语义也不因未理解而丢弃。
识别按元素与属性的 localname 进行，源文件带或不带默认命名空间皆可读；写出统一
带 TTML 默认命名空间。
"""

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path
from typing import override

from cx_studio.core import CxTime, TimeRange
from cx_studio.filesystem import detect_file_encoding

from ..errors import FormatError
from ..format import Format
from ..loader import SubtitleLoader
from ..model import SubtitleItem
from ..saver import SubtitleSaver
from ..timecodec import TimeCodec

__all__ = ["TtmlFormat", "TtmlLoader", "TtmlSaver"]

_TTML_NAMESPACE = "http://www.w3.org/ns/ttml"
_XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
_EXTRA_PREFIX = "ttml_"
_CLOCK_CODEC = TimeCodec("HH:MM:SS.mmm")
_RESERVED_ATTRIBUTES = frozenset({"begin", "end"})
_OFFSET_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)(?P<unit>ms|min|h|m|s)")
_OFFSET_UNIT_MILLISECONDS = {
    "h": 3_600_000,
    "m": 60_000,
    "min": 60_000,
    "s": 1_000,
    "ms": 1,
}


def _local_name(qualified: str) -> str:
    """取限定名的 localname（``{命名空间}名字`` → ``名字``）。

    Args:
        qualified: ElementTree 的限定名；不含命名空间时原样返回。

    Returns:
        str: 去掉命名空间花括号部分后的名字。
    """
    return qualified.rpartition("}")[2]


def _tag(namespace: str, name: str) -> str:
    """构造带命名空间的 ElementTree 标签名。

    Args:
        namespace: 命名空间 URI。
        name: 元素 localname。

    Returns:
        str: 形如 ``{命名空间}名字`` 的限定名。
    """
    return f"{{{namespace}}}{name}"


def _read_text(element: ET.Element) -> str:
    """拼接元素内的文本节点，``<br/>`` 元素转换为换行符。

    递归遍历全部子孙节点：普通子元素的文本并入结果，``<br/>`` 产出一个换行；
    每个子元素之后的 tail 文本按其位置追加，从而保持文档顺序。

    Args:
        element: 待读取的元素。

    Returns:
        str: 元素内文本依文档顺序拼接的结果，``<br/>`` 处为 ``\\n``。
    """
    parts: list[str] = [element.text or ""]
    for child in element:
        tag = child.tag
        if isinstance(tag, str):
            parts.append("\n" if _local_name(tag) == "br" else _read_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


class TtmlLoader(SubtitleLoader):
    """TTML 读向：从 ``<tt>`` 文档提取 ``<p>`` 条目。

    子集边界：只识别 ``<tt><body><div>`` 下的 ``<p>`` 元素，每个 ``<p>`` 产出一个
    条目，出现顺序即返回顺序。时间只接受 clock 字面量（``HH:MM:SS.mmm``，严格
    全串匹配）与带单位偏移字面量（十进制数 + ``h``/``m``/``min``/``s``/``ms``，
    如 ``10s``、``1.5s``、``100ms``）；帧数（``f``）、tick（``t``）等其余 TTML
    时间形式一律报错，不猜测换算规则。

    ``<p>`` 的文本取其全部子孙文本节点（嵌套 ``<span>`` 等一并拼接），``<br/>``
    转为换行，首尾空白去除；行内嵌套元素自带的独立时间不被建模，随外层 ``<p>``
    的时间走——这是文本子集的有意降级。``begin``/``end`` 之外的属性（``style``、
    ``region``、``xml:lang`` 等）原样写入条目的扩展位，键为 ``ttml_`` 加属性
    localname；TTML 无说话人语法，``speaker`` 恒为 None。

    识别按元素与属性的 localname 进行，源文件带或不带默认命名空间皆可读；根元素
    不是 ``tt`` 时视为非本格式而报错。
    """

    @override
    def load(self, path: Path) -> list[SubtitleItem]:
        """从 TTML 文件提取全部条目。

        Args:
            path: 来源文件路径。

        Returns:
            list[SubtitleItem]: 依 ``<p>`` 在文档中出现顺序排列的条目列表；
                文档不含 ``<p>`` 时为空列表。

        Raises:
            FormatError: 编码无法判定或按该编码解码失败、XML 解析失败（消息
                携带行列位置）、根元素不是 ``tt``，或 ``<p>`` 的时间字面量
                无法识别。
            OSError: 来源不可读等系统级失败。
        """
        encoding = detect_file_encoding(path)
        if not encoding:
            raise FormatError(f"无法判定 TTML 文件编码：{path}")
        try:
            content = path.read_text(encoding=encoding)
        except (LookupError, UnicodeError) as exc:
            raise FormatError(f"按 {encoding} 解码 TTML 文件失败：{path}") from exc
        if content.startswith("\ufeff"):
            content = content[1:]

        try:
            root = ET.fromstring(content)
        except ET.ParseError as exc:
            line, column = exc.position
            # expat 给出的列号从 0 起，FormatError 的列号契约从 1 起
            raise FormatError(f"TTML 解析失败：{exc}", line=line, column=column + 1) from exc

        root_name = _local_name(root.tag)
        if root_name != "tt":
            raise FormatError(f"根元素不是 TTML 的 tt：{root_name}")

        return [
            self._extract_item(element)
            for element in root.iter()
            if isinstance(element.tag, str) and _local_name(element.tag) == "p"
        ]

    def _extract_item(self, element: ET.Element) -> SubtitleItem:
        """把一个 ``<p>`` 元素转换为条目。

        Args:
            element: ``<p>`` 元素。

        Returns:
            SubtitleItem: 时间、文本与扩展属性提取自该元素的条目。

        Raises:
            FormatError: 缺少 ``begin``/``end`` 属性，或时间字面量无法识别。
        """
        attributes = {
            _local_name(name): value for name, value in element.attrib.items()
        }
        begin_raw = attributes.pop("begin", None)
        end_raw = attributes.pop("end", None)
        if begin_raw is None or end_raw is None:
            raise FormatError("TTML 的 p 元素缺少 begin/end 属性")
        start = self._parse_time(begin_raw)
        end = self._parse_time(end_raw)
        extra = {f"{_EXTRA_PREFIX}{name}": value for name, value in attributes.items()}
        return SubtitleItem(
            time_range=TimeRange(start, end - start),
            text=_read_text(element).strip(),
            extra=extra,
        )

    def _parse_time(self, raw: str) -> CxTime:
        """把 TTML 时间字面量解析为时间值。

        先尝试带单位偏移形式，再尝试 clock 形式；两者皆不匹配即报错，不做
        宽松兜底。偏移形式按 ``round(数值 × 单位毫秒数)`` 换算。

        Args:
            raw: 时间字面量原文。

        Returns:
            CxTime: 解析得到的时间值。

        Raises:
            FormatError: 字面量既非 clock 形式（``HH:MM:SS.mmm``）也非带单位
                偏移形式（如 ``10s``、``1.5s``、``100ms``）。
        """
        match = _OFFSET_PATTERN.fullmatch(raw)
        if match is not None:
            unit = match.group("unit")
            milliseconds = round(
                float(match.group("value")) * _OFFSET_UNIT_MILLISECONDS[unit]
            )
            return CxTime(milliseconds)
        try:
            return _CLOCK_CODEC.parse(raw)
        except FormatError as exc:
            raise FormatError(
                f"无法识别的 TTML 时间字面量：{raw!r}（仅接受 HH:MM:SS.mmm clock "
                "形式与带单位偏移形式，如 10s、1.5s、100ms）"
            ) from exc


class TtmlSaver(SubtitleSaver):
    """TTML 写向：把条目集合写为单个 TTML 文件。

    输出为 ``<tt xmlns="http://www.w3.org/ns/ttml" xml:lang="und">`` 下的
    ``<body><div>`` 结构，每个条目一个 ``<p>``；时间统一以 clock 字面量
    （``HH:MM:SS.mmm``）写出，条目文本中的换行还原为 ``<br/>``。输入按起始时刻
    稳定排序后顺序写出。TTML 可以表达交叠，故交叠原样保留、不拆分文件。

    条目的 ``ttml_`` 前缀扩展键还原为 ``<p>`` 属性（去掉前缀），其中
    ``begin``/``end`` 属保留名——时间由时间属性承载，故不写出；``ttml_`` 之外的
    扩展键、以及模型无对应结构的 ``speaker`` 一律不写，不猜测其表达方式。
    """

    @override
    def save(self, items: Iterable[SubtitleItem], target: Path) -> list[Path]:
        """把条目集合写出为单个 TTML 文件。

        Args:
            items: 待写出的条目可迭代序列；实现先物化并按起始时刻稳定排序。
            target: 目标文件路径。

        Returns:
            list[Path]: 单元素列表，即 ``target``。

        Raises:
            FormatError: ``target`` 已存在（写前预检，零输出，不覆盖既有文件）。
            OSError: 目标目录不可写等系统级失败。
        """
        if target.exists():
            raise FormatError(f"目标文件已存在：{target}")

        ordered = sorted(items, key=lambda item: item.start)
        ET.register_namespace("", _TTML_NAMESPACE)
        tt = ET.Element(
            _tag(_TTML_NAMESPACE, "tt"), {_tag(_XML_NAMESPACE, "lang"): "und"}
        )
        body = ET.SubElement(tt, _tag(_TTML_NAMESPACE, "body"))
        div = ET.SubElement(body, _tag(_TTML_NAMESPACE, "div"))
        for item in ordered:
            paragraph = ET.SubElement(
                div, _tag(_TTML_NAMESPACE, "p"), self._paragraph_attributes(item)
            )
            self._write_text(paragraph, item.text)

        ET.ElementTree(tt).write(target, encoding="utf-8", xml_declaration=True)
        return [target]

    def _paragraph_attributes(self, item: SubtitleItem) -> dict[str, str]:
        """构造 ``<p>`` 的属性表：时间与还原后的扩展属性。

        Args:
            item: 待写出的条目。

        Returns:
            dict[str, str]: 含 ``begin``/``end`` 与去前缀扩展键的属性映射；
                保留名与非 ``ttml_`` 前缀键被跳过。
        """
        attributes = {
            "begin": _CLOCK_CODEC.format(item.start),
            "end": _CLOCK_CODEC.format(item.time_range.end),
        }
        for key, value in item.extra.items():
            if not key.startswith(_EXTRA_PREFIX) or value is None:
                continue
            name = key[len(_EXTRA_PREFIX) :]
            if not name or name in _RESERVED_ATTRIBUTES:
                continue
            attributes[name] = value if isinstance(value, str) else str(value)
        return attributes

    def _write_text(self, paragraph: ET.Element, text: str) -> None:
        """把条目文本写入 ``<p>``，换行还原为 ``<br/>`` 元素。

        Args:
            paragraph: 目标 ``<p>`` 元素。
            text: 条目文本，``\\n`` 表示真实换行。
        """
        lines = text.split("\n")
        paragraph.text = lines[0]
        for line in lines[1:]:
            ET.SubElement(paragraph, _tag(_TTML_NAMESPACE, "br")).tail = line


# dfxp 是 TTML 的前身格式名，沿用同一适配器
TtmlFormat = Format(
    name="ttml",
    extensions=(".ttml", ".xml", ".dfxp"),
    loader=TtmlLoader(),
    saver=TtmlSaver(),
)
