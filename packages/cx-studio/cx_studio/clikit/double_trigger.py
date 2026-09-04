"""CLI 双击（双次触发）判定基础设施。

提供 ``DoubleTrigger``：基于时间窗判定连续两次触发属于“单击”还是
“双击”的事件组件，常用于“第一次中断提示、第二次确认退出”之类的
两级 CLI 交互。事件名应引用模块级常量（``TRIGGERED``/
``FIRST_TRIGGERED``/``SECOND_TRIGGERED``）而非裸字符串。
"""

from datetime import datetime

from pyee import EventEmitter

TRIGGERED: str = "triggered"
FIRST_TRIGGERED: str = "first_triggered"
SECOND_TRIGGERED: str = "second_triggered"


class DoubleTrigger(EventEmitter):
    """基于时间窗的双击触发判定器（事件发射器）。

    每次 ``trigger()`` 都无条件发射 ``TRIGGERED``，随后按“距上一次
    ``trigger()`` 是否不足 ``delay`` 秒”选择状态常量：不足则发射
    ``SECOND_TRIGGERED``（视为窗口内的再次触发），否则发射
    ``FIRST_TRIGGERED``（视为新一轮的第一次触发）。

    ``delay`` 为判定窗口长度（秒）。每次触发都会刷新时间基准，因此
    窗口内的连续多次触发会依次判为第二次、第三次……（均发射
    ``SECOND_TRIGGERED``），直到某次间隔超过 ``delay`` 后才重新计为
    ``FIRST_TRIGGERED``。``is_pending`` 反映当前时刻是否仍处于窗口内；
    判定基于墙钟时间实时计算，无后台定时器。
    """

    def __init__(self, delay: float = 3):
        super().__init__()
        self._delay = delay
        self._last_time = None

    @property
    def is_pending(self) -> bool:
        """当前是否处于双击判定窗口内。

        从未触发过时为 False；否则返回“距上次触发是否不足 ``delay``
        秒”。随时间推移自动过期（当前时刻与上次触发时刻之差不再小于
        ``delay``）。
        """
        if self._last_time is None:
            return False
        span = datetime.now() - self._last_time
        return span.total_seconds() < self._delay

    def trigger(self):
        """触发一次信号并判定单击或双击。

        顺序：无条件发射 ``TRIGGERED``；若处于窗口内（距上次触发不足
        ``delay`` 秒）发射 ``SECOND_TRIGGERED``，否则发射
        ``FIRST_TRIGGERED``；随后把本次触发时刻记为新的时间基准。
        事件名应使用模块级常量。
        """
        self.emit(TRIGGERED)

        if self.is_pending:
            self.emit(SECOND_TRIGGERED)
        else:
            self.emit(FIRST_TRIGGERED)

        self._last_time = datetime.now()
