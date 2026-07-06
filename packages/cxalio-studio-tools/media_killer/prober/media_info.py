"""MediaInfo 值对象模块。

承载 ffprobe 解析后的媒体元数据，是 MediaProber 和 MediaDB 之间的统一数据载体。
"""

from dataclasses import dataclass, asdict
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True)
class MediaInfo:
    """媒体元数据值对象。

    承载 ffprobe 解析后的媒体元数据，用于在 MediaProber 和 MediaDB 之间传递。
    提供序列化/反序列化方法，支持与 FileInfoCache 交互。

    Attributes:
        file_path: 该 MediaInfo 所属文件的路径
        container_format: 容器格式，如 "mov,mp4,m4a"
        stream_count: 流数量
        has_video: 是否包含视频流
        has_audio: 是否包含音频流
        duration: 时长（秒）
        width: 视频宽度（像素）
        height: 视频高度（像素）
        fps: 帧率，优先使用 Fraction 保留精确值
        video_codec: 视频编码格式，如 "h264"
        video_bitrate: 视频码率（bps）
        audio_codec: 音频编码格式，如 "aac"
        audio_bitrate: 音频码率（bps）
        sample_rate: 采样率（Hz）
        channels: 音频声道数
    """

    # 文件身份
    file_path: Path

    # 容器与流
    container_format: str | None = None
    stream_count: int = 0
    has_video: bool = False
    has_audio: bool = False

    # 时长（秒）
    duration: float | None = None

    # 视频属性
    width: int | None = None
    height: int | None = None
    fps: Fraction | float | None = None
    video_codec: str | None = None
    video_bitrate: int | None = None

    # 音频属性
    audio_codec: str | None = None
    audio_bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None

    def to_dict(self) -> dict:
        """序列化为字典，用于存入 FileInfoCache。

        将 Path 转换为字符串，将 Fraction 转换为字符串表示。

        Returns:
            序列化后的字典，可直接用于 FileInfoCache.set()
        """
        data = asdict(self)

        # Path -> str
        data["file_path"] = str(self.file_path)

        # Fraction -> str
        if isinstance(self.fps, Fraction):
            data["fps"] = str(self.fps)

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "MediaInfo":
        """从字典反序列化，用于从 FileInfoCache 读取。

        将字符串恢复为 Path，将字符串恢复为 Fraction。
        缺失字段使用默认值，保证旧缓存可向前兼容。

        Args:
            data: 从 FileInfoCache.get() 获取的字典

        Returns:
            反序列化后的 MediaInfo 实例
        """
        # 复制字典以避免修改原始数据
        kwargs = data.copy()

        # str -> Path
        if "file_path" in kwargs and isinstance(kwargs["file_path"], str):
            kwargs["file_path"] = Path(kwargs["file_path"])

        # str -> Fraction
        if "fps" in kwargs and isinstance(kwargs["fps"], str):
            try:
                kwargs["fps"] = Fraction(kwargs["fps"])
            except (ValueError, ZeroDivisionError):
                # 如果无法解析为 Fraction，保持原值（可能是 float 或 None）
                pass

        return cls(**kwargs)
