"""subtitler 的格式注册接线。

本模块是 subtitler 工具格式面的唯一来源：登记本工具启用的格式，并据此汇总
扩展名查表，供前台按文件后缀选择源/目标格式。

`subtitler.common` 层不设注册表、也不知道本工具登记了哪些格式——格式身份由
`Format` 对象携带，登记动作属于前台装配，换一个前台即可复用同一能力层服务
不同的格式子集。
"""

from pathlib import Path

from subtitler.common import Format
from subtitler.common.formats import CsvFormat, SrtFormat, TtmlFormat

FORMATS: dict[str, Format] = {
    SrtFormat.name: SrtFormat,
    TtmlFormat.name: TtmlFormat,
    CsvFormat.name: CsvFormat,
}
"""本工具启用的格式，键为格式名称、值为格式身份对象。"""

EXTENSION_TABLE: dict[str, Format] = {
    (extension if extension.startswith(".") else f".{extension}").lower(): fmt
    for fmt in FORMATS.values()
    for extension in fmt.extensions
}
"""扩展名 → 格式的查表，键为含点小写扩展名（如 ``".srt"``）。"""


def format_for(path: Path) -> Format | None:
    """按文件扩展名查表确定格式。

    Args:
        path: 待识别的文件路径。

    Returns:
        Format | None: 所识别出的格式；扩展名未登记时返回 None。
    """
    return EXTENSION_TABLE.get(path.suffix.lower())


__all__ = ["EXTENSION_TABLE", "FORMATS", "format_for"]
