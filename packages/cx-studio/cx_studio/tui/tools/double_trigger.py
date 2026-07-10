from datetime import datetime

from pyee import EventEmitter

TRIGGERED: str = "triggered"
FIRST_TRIGGERED: str = "first_triggered"
SECOND_TRIGGERED: str = "second_triggered"


class DoubleTrigger(EventEmitter):

    def __init__(self, delay: float = 3):
        super().__init__()
        self._delay = delay
        self._last_time = None

    @property
    def is_pending(self) -> bool:
        if self._last_time is None:
            return False
        span = datetime.now() - self._last_time
        return span.total_seconds() < self._delay

    def trigger(self):
        self.emit(TRIGGERED)

        if self.is_pending:
            self.emit(SECOND_TRIGGERED)
        else:
            self.emit(FIRST_TRIGGERED)

        self._last_time = datetime.now()
