from cx_tools.app import IAppEnvironment
from . import __version__


class AppEnv(IAppEnvironment):
    """MediaScout 应用环境。

    提供输出能力（say/whisper）。
    不持有 context——context 由 Application 通过构造参数注入。
    """

    def __init__(self):
        super().__init__()
        self.app_name = "MediaScout"
        self.app_version = __version__
