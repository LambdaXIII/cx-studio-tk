"""时间基准（Timebase）：帧率与丢帧标记的简单值对象。

用于 CxTime 与时间码（timecode）之间的帧换算：fps 为整帧率，
drop_frame 标记是否采用丢帧制时间码。
"""

from dataclasses import dataclass


@dataclass
class Timebase:
    """描述帧率与丢帧制标记的时间基准。

    字段语义：
        - ``fps``：整数帧率（每秒帧数），决定一帧的毫秒时长与时间码的
          帧号换算。
        - ``drop_frame``：是否为丢帧制（drop-frame）时间码。仅影响
          CxTime.to_timecode 输出的帧分隔符（``;`` 而非 ``:``），
          换算本身不做丢帧补偿。
    """

    fps: int = 24
    drop_frame: bool = False

    @classmethod
    def from_fps(cls, x: int | float):
        """从（可能为小数的）帧率值构造时间基准。

        帧率四舍五入为整数存入 fps；当入参与取整结果不一致时
        （即 x 为带小数的值，如 29.97），自动把 drop_frame 置为 True，
        否则为 False。

        Args:
            x: 帧率，可为整数或小数（如 24、29.97、23.976）。

        Returns:
            Timebase: 由 x 归一出的时间基准。
        """
        fps = int(round(x))
        drop_frame = fps != x
        return cls(fps=fps, drop_frame=drop_frame)

    @property
    def milliseconds_per_frame(self) -> int:
        """每帧对应的毫秒数。

        Returns:
            int: 1000 ÷ fps 四舍五入取整（如 24fps 为 42）。
        """
        a = 1000.0 / self.fps
        return int(round(a))
