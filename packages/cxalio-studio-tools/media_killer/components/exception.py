"""media_killer 异常定义。

定义应用级可恢复异常，由 Application.__exit__ 捕获并友好输出。
"""


class SafeError(Exception):
    """可恢复的应用异常。

    携带 Rich 样式名，由 Application.__exit__ 捕获后
    通过 console.print 以对应样式输出错误信息。

    Attributes:
        message: 错误消息文本
        style: Rich 样式名（默认 "cx.error"）
    """

    def __init__(self, message: str | None = None, style: str | None = None) -> None:
        """初始化 SafeError。

        Args:
            message: 错误消息文本
            style: Rich 样式名，默认 "cx.error"
        """
        super().__init__(message)
        self.message = message
        self.style = style or "cx.error"


class UserForceCancelError(SafeError):
    """用户强制取消异常。

    第二次 Ctrl+C 触发时抛出，表示用户明确要求中止所有操作。
    """

    pass
