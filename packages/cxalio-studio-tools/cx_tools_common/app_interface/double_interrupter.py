from datetime import datetime


class DoubleInterrupter:
    def __init__(self, force_delay: float = 3):
        self.wanna_quit = False
        self.really_wanna_quit = False
        self.last_time: datetime | None = None
        self._force_delay = force_delay
        self.when_wanna_quit = None
        self.when_really_wanna_quit = None

    def is_pending(self) -> bool:
        if not self.last_time:
            return False
        now = datetime.now()
        delay = now - self.last_time
        return delay.seconds < self._force_delay

    def trigger(self):
        if self.is_pending():
            self.really_wanna_quit = True
            if self.when_really_wanna_quit:
                self.when_really_wanna_quit()
        else:
            self.wanna_quit = True
            if self.when_wanna_quit:
                self.when_wanna_quit()

        self.last_time = datetime.now()
