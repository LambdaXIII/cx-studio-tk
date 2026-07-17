"""Jpegger 专用异常。

本模块定义了 MissionRunner 在任务执行过程中可能抛出的可恢复异常。
它们继承自 `SafeError`，会被应用生命周期的 `__exit__` 捕获并以
预设样式展示，不会打印完整的 Python 堆栈。
"""

from cx_tools.i18n import _
from cx_tools.app import SafeError


class NoSourceFileError(SafeError):
    """当指定的源文件不存在时抛出。"""

    def __init__(self, message: str | None = None, style: str | None = None):
        super().__init__(message or _("未找到源文件"), style or "red")


class TargetingSourceFileError(SafeError):
    """当目标路径与源路径相同、会导致源文件被覆盖时抛出。"""

    def __init__(self, message: str | None = None, style: str | None = None):
        super().__init__(message or _("源文件无法被目标文件所覆盖"), style or "red")
