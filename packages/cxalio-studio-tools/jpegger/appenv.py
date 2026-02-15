from cx_tools.app import IAppEnvironment
from .simple_appcontext import SimpleAppContext


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "Jpegger"
        self.app_version = "0.7.0"
        self.context: SimpleAppContext

    def is_debug_mode_on(self):
        return self.context.debug_mode


appenv = AppEnv()
