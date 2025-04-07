from dataclasses import dataclass, field

from pathlib import Path
from turtle import st

from ..core.cx_time import CxTime

from ..core.cx_filesize import FileSize


@dataclass(frozen=True)
class FFmpegFormatInfo:
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
            tags=data["tags"],
        )
