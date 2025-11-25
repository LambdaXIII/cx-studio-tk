from .format_info import FormatInfo
from .stream_info import StreamInfo
import cx_wealth.rich_types as r
from cx_wealth import WealthDetailTable, WealthLabel


class MediaInfo:
    def __init__(self, data: dict):
        self.data = data
        self.format_info = FormatInfo(data.get("format", {}))
        self.stream_infos = [StreamInfo(stream) for stream in data.get("streams", [])]

    def __rich_console__(self, console, options):
        o = options.update(highlight=False)
        table = WealthDetailTable(self.format_info, sub_box=False)

        labels = r.Group(*(WealthLabel(stream) for stream in self.stream_infos))
        stream_box = r.Panel(
            labels,
            title="流信息",
            title_align="left",
            border_style="dim",
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
