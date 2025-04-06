class SafeError(Exception):
    def __init__(self, message: str | None = None):
        self.message = message or "Unknown-But-Safe Error"


class UserForceCancelError(SafeError):
    def __init__(self, message: str | None = None):
        super().__init__(message or "User forced cancelling")
