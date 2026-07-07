"""MediaProber 模块。

纯 ffprobe 调用器，负责获取单个媒体文件的元数据并返回 MediaInfo 值对象。
无锁、无状态、支持并发。
"""

import subprocess
import json
from fractions import Fraction
from pathlib import Path

from .media_info import MediaInfo


class MediaProber:
    """纯 ffprobe 调用器。

    对单个文件调用 ffprobe，解析 JSON 输出并返回 MediaInfo 值对象。
    不内部持锁，支持并发运行；并发策略由调用方决定。
    """

    def __init__(
        self,
        ffprobe_executable: str | Path | None = None,
    ) -> None:
        """初始化 MediaProber。

        Args:
            ffprobe_executable: ffprobe 可执行文件路径。若为 None，则使用 "ffprobe"。
        """
        self._ffprobe = (
            str(ffprobe_executable) if ffprobe_executable is not None else "ffprobe"
        )

    def probe(self, file: Path) -> MediaInfo:
        """同步调用 ffprobe，返回 MediaInfo。

        Args:
            file: 要探测的媒体文件路径

        Returns:
            MediaInfo: 包含完整元数据的 MediaInfo 对象

        Raises:
            FileNotFoundError: 文件不存在
            RuntimeError: ffprobe 调用失败或解析失败
        """
        if not file.exists():
            raise FileNotFoundError(f"文件不存在: {file}")

        result = subprocess.run(
            [
                self._ffprobe,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(file),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"ffprobe 调用失败 (退出码 {result.returncode}): {result.stderr.strip()}"
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"ffprobe 输出解析失败: {e}") from e

        return self._parse(data, file)

    def _parse(self, data: dict, file: Path) -> MediaInfo:
        """将 ffprobe JSON 输出解析为 MediaInfo。

        Args:
            data: ffprobe 的 JSON 输出字典
            file: 被探测的文件路径

        Returns:
            解析后的 MediaInfo 对象
        """
        fmt = data.get("format", {})
        streams = data.get("streams", [])

        # 容器信息
        container_format: str | None = fmt.get("format_name")

        # 时长
        duration: float | None = None
        raw_duration = fmt.get("duration")
        if raw_duration is not None:
            try:
                duration = float(raw_duration)
            except (ValueError, TypeError):
                pass

        # 流统计
        stream_count = len(streams)
        video_stream = None
        audio_stream = None
        for s in streams:
            codec_type = s.get("codec_type")
            if codec_type == "video" and video_stream is None:
                video_stream = s
            elif codec_type == "audio" and audio_stream is None:
                audio_stream = s

        has_video = video_stream is not None
        has_audio = audio_stream is not None

        # 视频属性
        width: int | None = None
        height: int | None = None
        fps: Fraction | float | None = None
        video_codec: str | None = None
        video_bitrate: int | None = None

        if video_stream is not None:
            width = _safe_int(video_stream.get("width"))
            height = _safe_int(video_stream.get("height"))
            video_codec = video_stream.get("codec_name")
            video_bitrate = _safe_int(video_stream.get("bit_rate"))
            fps = _parse_fps(video_stream)

        # 音频属性
        audio_codec: str | None = None
        audio_bitrate: int | None = None
        sample_rate: int | None = None
        channels: int | None = None

        if audio_stream is not None:
            audio_codec = audio_stream.get("codec_name")
            audio_bitrate = _safe_int(audio_stream.get("bit_rate"))
            sample_rate = _safe_int(audio_stream.get("sample_rate"))
            channels = _safe_int(audio_stream.get("channels"))

        return MediaInfo(
            file_path=file,
            container_format=container_format,
            stream_count=stream_count,
            has_video=has_video,
            has_audio=has_audio,
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            video_codec=video_codec,
            video_bitrate=video_bitrate,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate,
            sample_rate=sample_rate,
            channels=channels,
        )


def _safe_int(value: object) -> int | None:
    """将 ffprobe 字段安全转换为 int。

    ffprobe 的数值字段可能是字符串或数字，N/A 表示不可用。

    Args:
        value: 待转换的值

    Returns:
        转换后的 int，或 None（无法转换时）
    """
    if value is None:
        return None
    try:
        v = int(value)  # type: ignore[arg-type]
        return v
    except (ValueError, TypeError):
        return None


def _parse_fps(stream: dict) -> Fraction | float | None:
    """从视频流中解析帧率。

    优先使用 avg_frame_rate，回退到 r_frame_rate。
    将 "30000/1001" 格式的字符串解析为 Fraction。

    Args:
        stream: ffprobe 视频流字典

    Returns:
        帧率（Fraction 或 float），无法解析时返回 None
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
