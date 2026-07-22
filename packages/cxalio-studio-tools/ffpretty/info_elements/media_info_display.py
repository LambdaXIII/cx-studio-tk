"""MediaInfoDisplay — 基于 media_killer.media.MediaInfo 的 Rich 渲染器。

提供探测模式的 Rich 终端输出，将 MediaInfo + StreamInfo 渲染为 ffpretty 风格的面板。
"""

from collections.abc import Generator

from cx_studio.core.file_size import FileSize
from cx_studio.core.cx_time import CxTime
from cx_wealthy import RichLabel, WealthyDetailTable, rich_types as r
from media_killer.media import MediaInfo, StreamInfo

# ── FormatSummary ──────────────────────────────────────────────


class FormatSummary:
    """容器格式摘要，实现 __rich_detail__ 供 WealthyDetailTable 渲染。"""

    def __init__(self, info: MediaInfo):
        self._info = info

    def __rich_detail__(self) -> Generator[tuple[str, object], None, None]:
        info = self._info

        # 文件名
        yield "文件名", r.Text(info.file_path.name, style="ffpretty.info.filename")

        # 编码代码（短格式名）
        if info.container_format:
            yield "编码代码", r.Text(
                info.container_format, style="ffpretty.info.format_name"
            )

        # 混流格式（长格式名）
        if info.container_long_name:
            yield "混流格式", r.Text(
                info.container_long_name, style="ffpretty.info.format_long_name"
            )

        # 时长
        if info.duration is not None:
            duration = CxTime.from_seconds(info.duration)
            yield "时长", r.Text(duration.pretty_string, style="ffpretty.info.duration")

        # 码率
        if info.bit_rate is not None:
            bitrate = FileSize.from_bytes(info.bit_rate)
            yield "码率", r.Text(
                f"{bitrate.pretty_string}/s", style="ffpretty.info.bit_rate"
            )

        # 文件大小
        if info.file_size is not None:
            size = FileSize.from_bytes(info.file_size)
            yield "大小", r.Text(size.pretty_string, style="ffpretty.info.file_size")


# ── StreamSummary ──────────────────────────────────────────────


class StreamSummary:
    """单流信息摘要，实现 __rich_label__ 供 RichLabel 渲染。

    对齐当前 StreamInfo.__rich_label__ 逻辑，基于 media_killer.media.StreamInfo 的 @property。
    """

    def __init__(self, stream: StreamInfo):
        self._stream = stream

    def __rich_label__(self) -> Generator[r.Text, None, None]:
        s = self._stream
        s_type = s.codec_type

        match s_type:
            case "video":
                yield r.Text(f"视频流 #{s.index}", style="ffpretty.info.stream_label")
            case "audio":
                yield r.Text(f"音频流 #{s.index}", style="ffpretty.info.stream_label")
            case "subtitle":
                yield r.Text(f"字幕流 #{s.index}", style="ffpretty.info.stream_label")
            case _:
                yield r.Text(f"未知流 #{s.index}", style="ffpretty.info.stream_label")

        if s.codec_name:
            yield r.Text(s.codec_name, style="ffpretty.info.codec_name")

        if s.profile:
            yield r.Text(f"[{s.profile}]", style="ffpretty.info.codec_name")

        if s.width and s.height:
            yield r.Text(f"{s.width}x{s.height}", style="cx.number")

        sar = s.sample_aspect_ratio
        if sar and sar != "1:1":
            yield r.Text(f"[{sar}]", style="cx.warning")
            if s.coded_width and s.coded_height:
                yield r.Text(f"({s.coded_width}x{s.coded_height})", style="cx.info")

        if s_type == "video":
            frame_rate = s.avg_frame_rate
            if frame_rate:
                yield r.Text(f"{frame_rate}fps", style="cx.whisper")

        if s_type == "audio":
            sample_rate = s.sample_rate
            if sample_rate:
                yield r.Text(f"{sample_rate}Hz", style="cx.whisper")
            channel_layout = s.channel_layout
            if channel_layout:
                yield r.Text(f"[{channel_layout}]", style="cx.info")

        if s.duration is not None:
            duration = CxTime.from_seconds(s.duration)
            yield r.Text(f"[{duration.to_timestamp()}]", style="cx.number")

        if s.bit_rate is not None:
            bitrate = FileSize.from_bytes(s.bit_rate)
            yield r.Text(f"{bitrate.pretty_string}/s", style="cx.error")


# ── MediaInfoDisplay ───────────────────────────────────────────


class MediaInfoDisplay:
    """基于 media_killer.media.MediaInfo 的 Rich 渲染器。"""

    def __init__(self, info: MediaInfo):
        self._info = info

    def __rich_console__(self, console, options):
        o = options.update(highlight=False)

        format_table = WealthyDetailTable(FormatSummary(self._info), sub_box=False)

        stream_labels = r.Group(
            *(RichLabel(StreamSummary(stream)) for stream in self._info.streams)
        )
        stream_box = r.Panel(
            stream_labels,
            title="流信息",
            title_align="left",
            border_style="ffpretty.info.border",
        )

        group = r.Group(format_table, stream_box)
        box = r.Panel(
            group,
            title="媒体信息",
            title_align="left",
            subtitle=self._info.file_path.name,
            subtitle_align="right",
        )
        return console.render(box, options=o)
