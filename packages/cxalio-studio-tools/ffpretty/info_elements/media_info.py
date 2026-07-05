from typing import Any

from cx_wealthy import rich_types as r
from cx_wealthy import WealthDetailTable, RichLabel
from .format_info import FormatInfo
from .stream_info import StreamInfo


class MediaInfo:
    def __init__(self, data: dict[str, Any]):
        self.data = data
        self.format_info = FormatInfo(data.get("format", {}))
        self.stream_infos = [StreamInfo(stream) for stream in data.get("streams", [])]

    def __rich_console__(self, console, options):
        o = options.update(highlight=False)
        table = WealthDetailTable(self.format_info, sub_box=False)

        labels = r.Group(*(RichLabel(stream) for stream in self.stream_infos))
        stream_box = r.Panel(
            labels,
            title="流信息",
            title_align="left",
            border_style="ffpretty.info.border",
        )

        group = r.Group(table, stream_box)
        box = r.Panel(
            group,
            title="媒体信息",
            title_align="left",
            subtitle=self.format_info.filename,
            subtitle_align="right",
        )
        return console.render(box, options=o)
