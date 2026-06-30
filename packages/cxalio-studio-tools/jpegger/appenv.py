"""Jpegger 全局应用环境。

`AppEnv` 继承 `IAppEnvironment`，提供 Rich 控制台、debug 输出门控
以及 Jpegger 特有的 `context` 字段。`context` 在 `JpeggerApp.start()`
中由 `SimpleAppContext.from_arguments()` 赋值。
"""

from typing import override

from cx_tools.app import IAppEnvironment

from .simple_appcontext import SimpleAppContext


class AppEnv(IAppEnvironment):
    """Jpegger 应用环境单例。

    Attributes:
        context: 当前命令行解析后的应用上下文；在 `start()` 之前为 None。
    """

    app_name: str
    app_version: str

    def __init__(self):
        super().__init__()
        self.app_name = "Jpegger"
        self.app_version = "0.8.1"
        self.context: SimpleAppContext | None = None

    @override
    def is_debug_mode_on(self) -> bool:
        """返回是否启用了调试输出。

        在 `start()` 完成前 context 尚未赋值，此时安全返回 False，
        避免在生命周期外调用时抛出 AttributeError。
        """
        if self.context is None:
            return False
        return self.context.debug_mode


appenv = AppEnv()
