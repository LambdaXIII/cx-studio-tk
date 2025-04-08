class FFmpegOutputParseError(RuntimeError):
    def __init__(self, message: str, output: str | None = None) -> None:
        super().__init__(message)
        self.output = output


class NoFFmpegExecutableError(RuntimeError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
