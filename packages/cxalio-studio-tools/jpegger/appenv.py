from cx_tools.app import IAppEnvironment
from collections.abc import Sequence
from .appcontext import AppContext


class AppEnv(IAppEnvironment):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__()
        self.app_name = "Jpegger"
        self.app_version = "0.1.0"
        self.app_context = AppContext.from_arguments(arguments)
