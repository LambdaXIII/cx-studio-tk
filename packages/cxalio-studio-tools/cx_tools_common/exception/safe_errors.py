class SafeError(Exception):
    def __init__(self, message: str | None = None):
        self.message = message or "Unknown-But-Safe Error"
