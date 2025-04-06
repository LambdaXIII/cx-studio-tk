import logging
import time
from collections.abc import Sequence

from rich.logging import RichHandler
from rich.progress import Progress

from cx_tools_common.app_interface import IAppEnvironment, ConfigManager
from .appcontext import AppContext
import importlib.resources
from rich.text import Text
from rich.table import Table


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "MediaKiller"
        self.app_version = "0.5.0"
        self.app_description = "媒体文件批量操作工具"
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
        self.progress.refresh()
        time.sleep(0.1)
        self.progress.stop()
        self.config_manager.remove_old_log_files()

    def show_banner(self, console=None):
        with importlib.resources.open_text("media_killer", "banner.txt") as banner:
            banner_text = Text(banner.read(), style="bold red")
        version_info = Text.from_markup(
            f"[bold blue]{self.app_name}[/] [yellow]v{self.app_version}[/]"
        )
        description = Text(self.app_description, style="dim")

        table = Table(box=None, show_header=False, show_footer=False, expand=True)

        table.add_column(justify="center", overflow="ellipsis")

        table.add_row(banner_text)
        table.add_row(version_info)
        table.add_row(description)
        console = console or self.console
        console.print(table)


appenv = AppEnv()
