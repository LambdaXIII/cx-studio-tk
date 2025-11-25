from typing import Any, Iterable
from cx_studio.core.cx_filesize import FileSize
from cx_studio.core.cx_time import CxTime
import cx_wealth.rich_types as r


class StreamInfo:
    def __init__(self, data: dict[str, Any]):
        self.data = data

    @property
    def stream_index(self) -> int:
        return self.data.get("index", -1)

    @property
    def codec_type(self) -> str:
        c_type = self.data.get("codec_type", None)
        return c_type

    @property
    def codec_name(self) -> str:
        return self.data.get("codec_name", None)

    @property
    def codec_long_names(self) -> Iterable[str]:
        c_long_name = self.data.get("codec_long_name", "")
        return c_long_name.split(" / ")

    def __rich_label__(self):
        index = self.stream_index
        s_type = self.codec_type
        match s_type:
            case "video":
                yield r.Text(f"视频流: {index}", style="blue")
            case "audio":
                yield r.Text(f"音频流: {index}", style="blue")
            case "subtitle":
                yield r.Text(f"字幕流: {index}", style="blue")
            case _:
                yield r.Text(f"未知流: {index}", style="blue")

        yield r.Text(self.codec_name, style="green1")
        profile = self.data.get("profile", None)
        if profile:
            yield r.Text(f"[{profile}]", style="green1")

        width, height = self.data.get("width", None), self.data.get("height", None)
        if width and height:
            yield r.Text(f"{width}x{height}", style="cx.number")

        sample_ratio = self.data.get("sample_aspect_ratio", None)
        if sample_ratio and sample_ratio != "1:1":
            yield r.Text(f"[{sample_ratio}]", style="cx.warning")
            cw, ch = self.data.get("coded_width", None), self.data.get(
                "coded_height", None
            )
            if cw and ch:
                yield r.Text(f"({cw}x{ch})", style="cx.info")

        if s_type == "video":
            frame_rate = self.data.get("avg_frame_rate", None)
            if frame_rate:
                yield r.Text(f"{frame_rate}fps", style="cx.whisper")

        if s_type == "audio":
            sample_rate = self.data.get("sample_rate", None)
            if sample_rate:
                yield r.Text(f"{sample_rate}Hz", style="cx.whisper")
            channel_layout = self.data.get("channel_layout", None)
            if channel_layout:
                yield r.Text(f"[{channel_layout}]", style="cx.info")

        duration_text = self.data.get("duration", None)
        if duration_text:
            duration = CxTime.from_seconds(float(duration_text))
            yield r.Text(f"[{duration.to_timestamp()}]", style="cx.number")

        bitrate_text = self.data.get("bit_rate", None)
        if bitrate_text:
            bitrate = FileSize.from_bytes(int(bitrate_text))
            yield r.Text(f"{bitrate.pretty_string}/s", style="cx.error")
