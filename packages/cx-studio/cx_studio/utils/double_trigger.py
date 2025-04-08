from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Literal


class DoubleTrigger:

    def __init__(self, delay: float = 3):
        self._delay = delay
        self._on_triggered = []
        self._on_first_triggered = []
        self._on_second_triggered = []
        self._last_time = None

    def on(self, event: Literal["triggered", "first_triggered", "second_triggered"]):
        def deco(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            if event == "triggered":
                self._on_triggered.append(wrapper)
            elif event == "first_triggered":
                self._on_first_triggered.append(wrapper)
            elif event == "second_triggered":
                self._on_second_triggered.append(wrapper)
            return wrapper

        return deco

    def install_trigger(
        self,
        event: Literal["triggered", "first_triggered", "second_triggered"],
        func: Callable,
    ):
        if event == "triggered":
            self._on_triggered.append(func)
        elif event == "first_triggered":
            self._on_first_triggered.append(func)
        elif event == "second_triggered":
            self._on_second_triggered.append(func)
        return self

    @property
    def is_pending(self):
        if self._last_time is None:
            return False
        span = datetime.now() - self._last_time
        return span.seconds < self._delay

    def trigger(self):
        for func in self._on_triggered:
            func()

        if self.is_pending:
            for func in self._on_second_triggered:
                func()
        else:
            for func in self._on_first_triggered:
                func()

        self._last_time = datetime.now()
