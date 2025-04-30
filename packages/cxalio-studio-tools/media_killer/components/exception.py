from cx_tools.app import SafeError


class UserForceCancelError(SafeError):
    def __init__(self, message: str | None = None):
        super().__init__(message or "User forced cancelling")
