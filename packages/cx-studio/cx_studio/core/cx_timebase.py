from dataclasses import dataclass


@dataclass
class Timebase:
    fps: int = 24
    drop_frame: bool = False

    @classmethod
    def from_fps(cls, x: int | float):
        fps = int(round(x))
        drop_frame = fps != x
        return cls(fps=fps, drop_frame=drop_frame)

    @property
    def milliseconds_per_frame(self) -> int:
        a = 1000.0 / self.fps
        return int(round(a))
