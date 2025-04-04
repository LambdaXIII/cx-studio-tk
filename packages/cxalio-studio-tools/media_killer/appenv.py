import logging
from collections.abc import Sequence

from rich.logging import RichHandler
from rich.progress import Progress

from cx_tools_common.app_interface import IAppEnvironment, ConfigManager
from .appcontext import AppContext


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "MediaKiller"
        self.app_version = "0.5.0"
        self.context: AppContext = AppContext()
        self.progress = Progress()
        self.console = self.progress.console
        self.config_manager = ConfigManager(self.app_name)

    def is_debug_mode_on(self):
        return self.context.debug_mode

    def load_arguments(self, arguments: Sequence[str] | None = None):
        self.context = AppContext.from_arguments(arguments)

    def start(self):
        self.progress.start()

    def stop(self):
        self.progress.stop()
        self.config_manager.remove_old_log_files()


appenv = AppEnv()
