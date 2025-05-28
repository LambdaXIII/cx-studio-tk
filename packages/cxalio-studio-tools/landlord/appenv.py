from cx_tools.app import IAppEnvironment
from cx_tools.app.config_manager import ConfigManager


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "landlord"
        self.app_version = "0.1.0"
        self.config_manager = ConfigManager(self.app_name)


appenv = AppEnv()
