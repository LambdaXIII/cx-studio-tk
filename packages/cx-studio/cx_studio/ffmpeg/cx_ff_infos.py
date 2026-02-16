import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from cx_studio.core import CxTime, FileSize


# @dataclass(frozen=True)
class FFmpegFormatInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
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
    def from_format_dict(cls, data: dict):
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
class FFmpegProcessInfo(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        #   frozen=True
    )

    bin: str
    args: list[str]
    start_time: datetime | None = None
    end_time: datetime | None = None
    media_duration: CxTime | None = None

    @property
    def started(self) -> bool:
        return self.start_time is not None

    @property
    def finished(self) -> bool:
        return self.end_time is not None


# @dataclass
class FFmpegCodingInfo(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        #   frozen=True
    )

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
    def parse_status_line(line: str) -> dict:
        datas: dict[str, Any] = {"raw_input": line.strip()}

        duration_match = re.search(
            r"Duration:\s*(?P<duration>\d+:\d+:\d+[:;.,]\d+)", line
        )
        if duration_match:
            # print("Duration match")
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
    def from_status_line(cls, line: str) -> "FFmpegCodingInfo":
        datas = cls.parse_status_line(line)
        return cls(**datas)

    def update_from_status_line(self, line: str) -> "FFmpegCodingInfo":
        datas = self.parse_status_line(line)
        return self.update(**datas)

    def update(self, **kwargs) -> "FFmpegCodingInfo":
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
