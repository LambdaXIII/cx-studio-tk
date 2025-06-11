from cx_tools.app import IAppEnvironment
from collections.abc import Sequence
from .appcontext import AppContext


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "Jpegger"
        self.app_version = "0.5.1"
        self.context: AppContext


appenv = AppEnv()
