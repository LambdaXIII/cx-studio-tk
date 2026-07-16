"""MediaProber 模块。

纯 ffprobe 调用器，负责获取单个媒体文件的元数据并返回 MediaInfo 值对象。
无锁、无状态、支持并发。
"""

import subprocess
import json
from pathlib import Path

from cx_studio.filesystem.cx_file_sizer import FileSizer
from .media_info import MediaInfo, StreamInfo, _safe_int


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
        self._sizer = FileSizer()

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
            encoding="utf-8",
            errors="replace",
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

        # FileSizer 兜底：ffprobe 未提供 size 时回退
        file_size = _safe_int(fmt.get("size"))
        if file_size is None:
            file_size = self._sizer.get_bytes(file)
            fmt["size"] = str(file_size)  # 写回 raw，保证 property 一致性

        # 构造 streams
        streams_data = [StreamInfo(raw=s) for s in data.get("streams", [])]

        return MediaInfo(
            raw=fmt,
            file_path=file,
            streams=streams_data,
        )
