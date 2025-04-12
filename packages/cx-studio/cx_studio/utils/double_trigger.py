from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Literal
from pyee import EventEmitter


class DoubleTrigger(EventEmitter):

    def __init__(self, delay: float = 3):
        super().__init__()
        self._delay = delay
        self._last_time = None

    @property
    def is_pending(self):
        if self._last_time is None:
            return False
        span = datetime.now() - self._last_time
        return span.seconds < self._delay

    def trigger(self):
        self.emit("triggered")

        if self.is_pending:
            self.emit("second_triggered")
        else:
            self.emit("first_triggered")

        self._last_time = datetime.now()
