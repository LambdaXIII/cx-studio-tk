import logging
from dataclasses import dataclass

from rich.logging import RichHandler

from common.ConfigManager import ConfigManager
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

    @property
    def app_name(self):
        return self.__APP_NAME

    @property
    def logger(self):
        return logging.getLogger(self.app_name)

    def start_app(self):
        if self.context.debug:
            self.logger.addHandler(
                RichHandler(level=logging.DEBUG, markup=True, rich_tracebacks=True)
            )


app = Application()
