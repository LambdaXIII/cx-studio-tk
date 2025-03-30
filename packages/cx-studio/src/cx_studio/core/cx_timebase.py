from dataclasses import dataclass
from numbers import Number


class Timebase:
    def __init__(self, fps: Number = 24, drop_frame: bool = None):
        self.fps = int(round(fps))
        self.drop_frame = drop_frame

        if self.fps != fps and drop_frame is None:
            self.drop_frame = True

    @property
    def milliseconds_per_frame(self) -> int:
        a = 1000.0 / self.fps
        return int(round(a))
