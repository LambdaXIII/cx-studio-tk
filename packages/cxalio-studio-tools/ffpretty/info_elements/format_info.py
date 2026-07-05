from pathlib import Path
from typing import Any

from cx_wealthy import rich_types as r
from cx_studio.core.cx_filesize import FileSize
from cx_studio.core.cx_time import CxTime


class FormatInfo:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    @property
    def format_name(self) -> str | None:
        return self.data.get("format_name", None)

    @property
    def format_long_name(self) -> str:
        return self.data.get("format_long_name", "")

    @property
    def duration(self) -> CxTime | None:
        duration_text = self.data.get("duration", None)
        if duration_text:
            return CxTime.from_seconds(float(duration_text))
        return None

    @property
    def bit_rate(self) -> FileSize | None:
        bit_rate_text = self.data.get("bit_rate", None)
        if bit_rate_text:
            return FileSize.from_bytes(int(bit_rate_text))
        return None

    @property
    def size(self) -> FileSize | None:
        size_text = self.data.get("size", None)
        if size_text:
            return FileSize.from_bytes(int(size_text))
        return None

    @property
    def streams(self) -> int:
        return self.data.get("nb_streams", 0)

    @property
    def filename(self) -> str | None:
        name = self.data.get("filename", None)
        if not name:
            return None
        return Path(name).name

    def __rich_detail__(self):
        name = self.filename
        if name:
            yield "文件名", r.Text(name, style="ffpretty.info.filename")

        format_name = self.format_name
        if format_name:
            yield "编码代码", r.Text(format_name, style="ffpretty.info.format_name")

        format_long_name = self.format_long_name
        if format_long_name:
            yield "混流格式", r.Text(
                format_long_name, style="ffpretty.info.format_long_name"
            )

        duration = self.duration
        if duration:
            yield "时长", r.Text(duration.pretty_string, style="ffpretty.info.duration")

        bit_rate = self.bit_rate
        if bit_rate:
            yield "码率", r.Text(
                f"{bit_rate.pretty_string}/s", style="ffpretty.info.bit_rate"
            )

        size = self.size
        if size:
            yield "大小", r.Text(size.pretty_string, style="ffpretty.info.file_size")
