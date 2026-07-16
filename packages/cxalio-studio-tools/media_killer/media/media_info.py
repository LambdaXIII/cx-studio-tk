"""MediaInfo 值对象模块。

承载 ffprobe 解析后的媒体元数据，是 MediaProber 和 MediaDB 之间的统一数据载体。
提供序列化/反序列化方法，支持与 FileInfoCache 交互。
"""

from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path


def _safe_int(value: object) -> int | None:
    """将 ffprobe 字段安全转换为 int。

    ffprobe 输出的数值字段可能为字符串（如 "1920"），也可能为 None
    或格式异常。此函数将值安全转换为 int，失败时返回 None。

    Args:
        value: ffprobe 字段的原始值

    Returns:
        转换后的整数，或 None
    """
    if value is None:
        return None
    try:
        v = int(value)  # type: ignore[arg-type]
        return v
    except (ValueError, TypeError):
        return None


def _safe_float(value: object) -> float | None:
    """将 ffprobe 字段安全转换为 float。

    Args:
        value: ffprobe 字段的原始值

    Returns:
        转换后的浮点数，或 None
    """
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None


# ── StreamInfo ─────────────────────────────────────────────────


@dataclass(frozen=True)
class StreamInfo:
    """单个媒体流的元数据。raw 为 ffprobe 该流对象的完整 JSON dict，唯一数据源。

    所有属性均为 @property 透读 raw，无数据冗余。
    """

    raw: dict

    # ── 标识 ──
    @property
    def index(self) -> int:
        return self.raw.get("index", 0)

    @property
    def codec_type(self) -> str:
        return self.raw.get("codec_type", "")

    @property
    def codec_name(self) -> str:
        return self.raw.get("codec_name", "")

    @property
    def codec_long_name(self) -> str | None:
        return self.raw.get("codec_long_name")

    @property
    def codec_tag_string(self) -> str | None:
        return self.raw.get("codec_tag_string")

    @property
    def profile(self) -> str | None:
        return self.raw.get("profile")

    @property
    def level(self) -> int | None:
        return _safe_int(self.raw.get("level"))

    # ── 视频 ──
    @property
    def width(self) -> int | None:
        return _safe_int(self.raw.get("width"))

    @property
    def height(self) -> int | None:
        return _safe_int(self.raw.get("height"))

    @property
    def coded_width(self) -> int | None:
        return _safe_int(self.raw.get("coded_width"))

    @property
    def coded_height(self) -> int | None:
        return _safe_int(self.raw.get("coded_height"))

    @property
    def pix_fmt(self) -> str | None:
        return self.raw.get("pix_fmt")

    @property
    def sample_aspect_ratio(self) -> str | None:
        return self.raw.get("sample_aspect_ratio")

    @property
    def display_aspect_ratio(self) -> str | None:
        return self.raw.get("display_aspect_ratio")

    @property
    def r_frame_rate(self) -> str | None:
        return self.raw.get("r_frame_rate")

    @property
    def avg_frame_rate(self) -> str | None:
        return self.raw.get("avg_frame_rate")

    @property
    def field_order(self) -> str | None:
        return self.raw.get("field_order")

    # ── 音频 ──
    @property
    def sample_fmt(self) -> str | None:
        return self.raw.get("sample_fmt")

    @property
    def sample_rate(self) -> int | None:
        return _safe_int(self.raw.get("sample_rate"))

    @property
    def channels(self) -> int | None:
        return _safe_int(self.raw.get("channels"))

    @property
    def channel_layout(self) -> str | None:
        return self.raw.get("channel_layout")

    @property
    def bits_per_sample(self) -> int | None:
        return _safe_int(self.raw.get("bits_per_sample"))

    # ── 通用 ──
    @property
    def duration(self) -> float | None:
        return _safe_float(self.raw.get("duration"))

    @property
    def bit_rate(self) -> int | None:
        return _safe_int(self.raw.get("bit_rate"))

    def nb_frames(self) -> int | None:
        return _safe_int(self.raw.get("nb_frames"))

    @property
    def start_time(self) -> float | None:
        return _safe_float(self.raw.get("start_time"))

    @property
    def time_base(self) -> str | None:
        return self.raw.get("time_base")

    # ── 元数据透传 ──
    @property
    def disposition(self) -> dict | None:
        return self.raw.get("disposition")

    @property
    def tags(self) -> dict | None:
        return self.raw.get("tags")


# ── 帧率解析 ──────────────────────────────────────────────────


def _parse_fps(stream: dict) -> Fraction | float | None:
    """从视频流中解析帧率。

    优先使用 avg_frame_rate，其次 r_frame_rate。
    返回 Fraction 保留精确值，无法解析时返回 float 兜底。

    Args:
        stream: 视频流 dict

    Returns:
        Fraction | float | None: 帧率值或 None
    """
    for key in ("avg_frame_rate", "r_frame_rate"):
        raw = stream.get(key)
        if raw is None or raw == "0/0" or raw == "0":
            continue
        try:
            return Fraction(raw)
        except (ValueError, ZeroDivisionError):
            continue
    return None


# ── MediaInfo ──────────────────────────────────────────────────


@dataclass(frozen=True)
class MediaInfo:
    """媒体元数据值对象。

    raw 为 ffprobe "format" 节点的完整 JSON dict，是 format 层属性的唯一数据源。
    streams 为逐流的 StreamInfo 列表，保留每一条流的完整信息。
    跨流计算的属性（has_video、width、fps 等）遍历 streams 动态聚合。

    提供序列化/反序列化方法，支持与 FileInfoCache 交互。
    """

    raw: dict
    file_path: Path
    streams: list[StreamInfo] = field(default_factory=list)

    # ── format 层透传 ──
    @property
    def container_format(self) -> str | None:
        return self.raw.get("format_name")

    @property
    def container_long_name(self) -> str | None:
        return self.raw.get("format_long_name")

    @property
    def duration(self) -> float | None:
        return _safe_float(self.raw.get("duration"))

    @property
    def bit_rate(self) -> int | None:
        return _safe_int(self.raw.get("bit_rate"))

    @property
    def file_size(self) -> int | None:
        return _safe_int(self.raw.get("size"))

    @property
    def stream_count(self) -> int:
        return len(self.streams)

    # ── 跨流计算 ──
    @property
    def has_video(self) -> bool:
        return any(s.codec_type == "video" for s in self.streams)

    @property
    def has_audio(self) -> bool:
        return any(s.codec_type == "audio" for s in self.streams)

    @property
    def width(self) -> int | None:
        for s in self.streams:
            if s.codec_type == "video":
                return s.width
        return None

    @property
    def height(self) -> int | None:
        for s in self.streams:
            if s.codec_type == "video":
                return s.height
        return None

    @property
    def fps(self) -> Fraction | float | None:
        for s in self.streams:
            if s.codec_type == "video":
                return _parse_fps(s.raw)
        return None

    @property
    def video_codec(self) -> str | None:
        for s in self.streams:
            if s.codec_type == "video":
                return s.codec_name
        return None

    @property
    def video_bitrate(self) -> int | None:
        for s in self.streams:
            if s.codec_type == "video":
                return s.bit_rate
        return None

    @property
    def audio_codec(self) -> str | None:
        for s in self.streams:
            if s.codec_type == "audio":
                return s.codec_name
        return None

    @property
    def audio_bitrate(self) -> int | None:
        for s in self.streams:
            if s.codec_type == "audio":
                return s.bit_rate
        return None

    @property
    def sample_rate(self) -> int | None:
        for s in self.streams:
            if s.codec_type == "audio":
                return s.sample_rate
        return None

    @property
    def channels(self) -> int | None:
        for s in self.streams:
            if s.codec_type == "audio":
                return s.channels
        return None

    # ── 元数据 ──
    @property
    def tags(self) -> dict | None:
        return self.raw.get("tags")

    # ── 序列化 ──
    def to_dict(self) -> dict:
        """序列化为字典，用于存入 FileInfoCache。

        Returns:
            序列化后的字典，可直接用于 FileInfoCache.set()
        """
        return {
            "raw": self.raw,
            "file_path": str(self.file_path),
            "streams": [{"raw": s.raw} for s in self.streams],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MediaInfo":
        """从字典反序列化，用于从 FileInfoCache 读取。

        旧缓存不含 raw 字段时回退为 {}（会丢失缓存数据，需重新探测）。
        旧缓存不含 streams 时默认为 []。

        Args:
            data: 从 FileInfoCache.get() 获取的字典

        Returns:
            反序列化后的 MediaInfo 实例
        """
        raw = data.get("raw", {})
        file_path = data.get("file_path", "")
        streams_raw = data.get("streams", [])

        if isinstance(file_path, str):
            file_path = Path(file_path)

        return cls(
            raw=raw,
            file_path=file_path,
            streams=[StreamInfo(raw=s["raw"]) for s in streams_raw],
        )
