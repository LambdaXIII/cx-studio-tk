"""Jpegger 全局应用环境。

`JpeggerEnv` 继承 `IAppEnvironment`，提供 Rich 控制台、debug 输出门控。
"""

from cx_tools.app import IAppEnvironment

from . import __version__


class JpeggerEnv(IAppEnvironment):
    """Jpegger 应用环境单例。"""

    app_name: str
    app_version: str

    def __init__(self):
        super().__init__()
        self.app_name = "Jpegger"
        self.app_version = __version__

    # is_debug_mode_on() 由基类 IAppEnvironment 通过 set_debug_mode 管理，
    # 不再在此处覆盖。


appenv = JpeggerEnv()
