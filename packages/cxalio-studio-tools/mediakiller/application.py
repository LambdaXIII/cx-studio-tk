import logging
from dataclasses import dataclass
from rich.console import Console
from rich.logging import RichHandler

from common import ConfigManager
from cx_studio.core import DataPackage
import click


@dataclass
class AppContext:
    presets = []
    sources = []
    script_output = None
    pretending_mode = False
    debug = False
    sort_mode = "x"
    continue_mode = False

    def __rich_repr__(self):
        yield "Presets", self.presets
        yield "Sources", self.sources
        yield "ExportScript", self.script_output
        yield "Sort Mode", self.sort_mode
        if self.pretending_mode:
            yield "Pretending Mode"
        if self.debug:
            yield "Debug Mode"
        if self.continue_mode:
            yield "Continue last task"


class Application:
    __APP_NAME = "MediaKiller"
    __APP_VERSION = "0.5.0"

    def __init__(self):
        self.context = AppContext()
        self.config_manager = ConfigManager(self.app_name)
        logging.basicConfig(
            filename=self.config_manager.new_log_file(),
            filemode="w",
            level=logging.NOTSET,
            format="%(message)s",
            datefmt="[%X]",
        )
        self.console = Console()

    @property
    def app_name(self):
        return self.__APP_NAME

    @property
    def logger(self):
        return logging.getLogger(self.app_name)

    def say(self, *args):
        self.console.print(*args)
        for arg in args:
            self.logger.info(arg)

    def whisper(self, *args):
        if self.context.debug:
            self.console.log(*args)
        for arg in args:
            self.logger.info(arg)

    def start_app(self):
        if self.context.debug:
            self.logger.addHandler(
                RichHandler(level=logging.DEBUG, markup=True, rich_tracebacks=True)
            )
        self.whisper("运行参数：", self.context)
        self.whisper("初始化完毕")

    def end_app(self):
        self.config_manager.remove_old_log_files()
        self.whisper("应用程序退出")

    def __enter__(self):
        self.start_app()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end_app()
        return False


app = Application()
