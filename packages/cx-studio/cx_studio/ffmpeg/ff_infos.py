"""FFmpeg 信息数据类。

定义描述 FFmpeg 媒体信息与转码运行状态的三个数据类：
- ``FFmpegFormatInfo``：承载 ffprobe 报告的容器格式信息（不可变）；
- ``FFmpegProcessInfo``：记录一次 FFmpeg 进程调用的执行状态；
- ``FFmpegCodingInfo``：实时编码/转码状态，可从 ffmpeg stderr 的
  状态/进度行解析与增量更新。
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Self


from cx_studio.core import CxTime, FileSize


@dataclass(frozen=True)
class FFmpegFormatInfo:
    """ffprobe 报告的单媒体容器格式信息（不可变数据类）。

    承载 ffprobe 探测输出中 format 层（如 ``ffprobe -show_format`` 的
    ``format`` 段）报告的信息：文件名、流数量、格式短/长名、起始时间、
    时长、大小、码率、探测评分与标签。时间字段由秒数转换为 ``CxTime``，
    大小/码率字段由字节数转换为 ``FileSize``；``tags`` 缺省为空 dict。
    实例不可变（``frozen=True``），可安全共享。
    """

    filename: Path
    streams: int | None = None
    format_name: str | None = None
    format_long_name: str | None = None
    start_time: CxTime | None = None
    duration: CxTime | None = None
    size: FileSize | None = None
    bit_rate: FileSize | None = None
    probe_score: int | None = None
    tags: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_format_dict(cls, data: dict[str, Any]) -> Self:
        """从 ffprobe 的 format 字典构造 ``FFmpegFormatInfo``。

        必需键以直接索引方式读取，缺失即抛错；``tags`` 用 ``.get``
        读取，缺失时取空 dict。时间/大小/码率等字符串数值在此完成
        到 ``CxTime``/``FileSize`` 的类型转换。

        Args:
            data: ffprobe 输出的 format 段字典，须含 ``filename``、
                ``nb_streams``、``format_name``、``format_long_name``、
                ``start_time``、``duration``、``size``、``bit_rate``、
                ``probe_score`` 键。

        Returns:
            新构造的 ``FFmpegFormatInfo`` 实例。

        Raises:
            KeyError: 上述必需键缺失。
            ValueError: 数值字段（时间/大小/码率/探测评分）无法转换。
        """
        return cls(
            filename=Path(data["filename"]),
            streams=int(data["nb_streams"]),
            format_name=data["format_name"],
            format_long_name=data["format_long_name"],
            start_time=CxTime.from_seconds(float(data["start_time"])),
            duration=CxTime.from_seconds(float(data["duration"])),
            size=FileSize.from_bytes(int(data["size"])),
            bit_rate=FileSize.from_bytes(int(data["bit_rate"])),
            probe_score=int(data["probe_score"]),
            tags=data.get("tags", {}),
        )


@dataclass
class FFmpegProcessInfo:
    """一次 FFmpeg 进程调用的记录数据类。

    承载一次调用的描述与执行状态：可执行文件（``bin``）、命令行参数
    （``args``），以及由调用方回填的进程启动/结束时刻与媒体总时长。
    本类不负责启动进程；``started``/``finished`` 分别以
    ``start_time``/``end_time`` 是否已设置来判定。
    """

    bin: str
    args: list[str]
    start_time: datetime | None = None
    end_time: datetime | None = None
    media_duration: CxTime | None = None

    @property
    def started(self) -> bool:
        """进程是否已启动（``start_time`` 已设置）。"""
        return self.start_time is not None

    @property
    def finished(self) -> bool:
        """进程是否已结束（``end_time`` 已设置）。"""
        return self.end_time is not None


@dataclass
class FFmpegCodingInfo:
    """FFmpeg 转码/编码过程状态数据类（可增量更新）。

    承载可从 ffmpeg stderr 的状态/进度行解析出的实时编码状态：当前帧号、
    帧率、量化参数 ``q``、已编码大小、当前/总时间、码率、速度等；
    未在某行中出现的字段保持构造时默认值（注意 ``current_q`` 默认
    ``-1``，其余数值字段默认 ``0``）。``raw_input`` 保存最近一次解析的
    原始行文本，``created`` 记录实例创建时刻。字段通过 ``update()`` 按
    “真实存在的属性才写入”的规则合并，因此不同行解析出的字段子集可安全
    累积到同一实例。
    """

    current_frame: int = 0
    current_fps: float = 0
    current_q: float = -1
    current_size: FileSize = field(default_factory=lambda: FileSize(0))
    current_time: CxTime = field(default_factory=lambda: CxTime(0))
    total_time: CxTime | None = field(default=None)
    current_bitrate: FileSize = field(default_factory=lambda: FileSize(0))
    current_speed: float = 0.0
    raw_input: str = ""
    created: datetime = field(default_factory=lambda: datetime.now())

    @staticmethod
    def parse_status_line(line: str) -> dict[str, Any]:
        """解析一行 ffmpeg stderr 状态/进度文本，返回命中的字段。

        行内片段均可选，命中才写入结果（进度行形如
        ``frame= 123 fps= 58 q= 28.0 size= 1024kB time= 00:00:12.34
        bitrate= 523.2kbits/s speed= 2.5x``）：
        - ``Duration: HH:MM:SS[.小]`` → ``total_time``（总时长行）；
        - ``frame=N`` / ``fps=N`` / ``q=N`` → ``current_frame`` /
          ``current_fps`` / ``current_q``；
        - ``L?size= 数值 单位``（``L`` 前缀出现于收尾行） →
          ``current_size``；
        - ``time=HH:MM:SS[.小]`` → ``current_time``；
        - ``bitrate= 数值 单位/s`` → ``current_bitrate``；
        - ``speed=Nx`` → ``current_speed``。
        时间戳为 ``时:分:秒`` 加小数部分，小数分隔符 ``:;.,`` 均可。
        ``raw_input`` 恒为去除首尾空白后的整行原文。

        Args:
            line: 待解析的 stderr 状态/进度行文本。

        Returns:
            解析结果 dict：键与字段同名，未匹配的字段不出现
            （``raw_input`` 恒存在）。
        """
        datas: dict[str, Any] = {"raw_input": line.strip()}

        duration_match = re.search(
            r"Duration:\s*(?P<duration>\d+:\d+:\d+[:;.,]\d+)", line
        )
        if duration_match:
            datas["total_time"] = CxTime.from_timestamp(
                duration_match.group("duration")
            )

        frames_match = re.search(r"frame=\s*(?P<frames>\d+)", line)
        if frames_match:
            datas["current_frame"] = int(frames_match.group("frames"))

        fps_match = re.search(r"fps=\s*(?P<fps>\d+(\.\d+)?)", line)
        if fps_match:
            datas["current_fps"] = float(fps_match.group("fps"))

        q_match = re.search(r"q=\s*(?P<q>-?\d+(\.\d+)?)", line)
        if q_match:
            datas["current_q"] = float(q_match.group("q"))

        size_match = re.search(r"L?size=\s*(?P<size>\d+(\.\d+)?\s*\w+)", line)
        if size_match:
            datas["current_size"] = FileSize.from_string(size_match.group("size"))

        time_match = re.search(r"time=\s*(?P<time>\d+:\d+:\d+[:;.,]\d+)", line)
        if time_match:
            datas["current_time"] = CxTime.from_timestamp(time_match.group("time"))

        bitrate_match = re.search(r"bitrate=\s*(?P<bitrate>\d+(\.\d+)?\s*\w+)/s", line)
        if bitrate_match:
            datas["current_bitrate"] = FileSize.from_string(
                bitrate_match.group("bitrate")
            )

        speed_match = re.search(r"speed=\s*(?P<speed>\d+(\.\d+)?)x", line)
        if speed_match:
            datas["current_speed"] = float(speed_match.group("speed"))

        return datas

    @classmethod
    def from_status_line(cls, line: str) -> Self:
        """从一行状态文本构造全新的 ``FFmpegCodingInfo``。

        等价于 ``cls(**cls.parse_status_line(line))``；行中未出现的字段
        采用类默认值（如 ``current_q`` 为 -1）。

        Args:
            line: 待解析的 stderr 状态/进度行文本。

        Returns:
            基于该行内容新建的 ``FFmpegCodingInfo`` 实例。
        """
        datas = cls.parse_status_line(line)
        return cls(**datas)

    def update_from_status_line(self, line: str) -> Self:
        """用一行状态文本更新当前实例并返回自身。

        内部复用 ``parse_status_line`` 与 ``update``：解析出的字段覆盖到
        本实例，行中未出现的字段保持不变。适合对同一实例逐行累积进度。

        Args:
            line: 待解析的 stderr 状态/进度行文本。

        Returns:
            更新后的自身（支持链式调用）。
        """
        datas = self.parse_status_line(line)
        return self.update(**datas)

    def update(self, **kwargs: Any) -> Self:
        """按字段名批量更新实例属性并返回自身。

        仅当 ``hasattr`` 为真（属性/字段真实存在）时才写入，未知键被
        静默忽略——因此解析器在不同行上给出的字段子集可安全合并，
        也可传入额外无关键而不报错。

        Args:
            **kwargs: 字段名到新值的映射。

        Returns:
            更新后的自身（支持链式调用）。
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
