from cx_tools.app import SafeError


class NoSourceFileError(SafeError):
    def __init__(self, message: str | None = None, style: str | None = None):
        super().__init__(message or "未找到源文件", style or "red")


class TargetingSourceFileError(SafeError):
    def __init__(self, message: str | None = None, style: str | None = None):
        super().__init__(message or "源文件无法被目标文件所覆盖", style or "red")
