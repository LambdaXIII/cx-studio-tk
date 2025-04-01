import logging
from argparse import ArgumentParser

from rich.progress import Progress

from common import ConfigManager
from mediakiller.appcontext import AppContext
from .appcontext_parser import AppContextParser


class AppServer:
    def __init__(self):
        self.context = None
        self.progress = Progress()
        self.console = self.progress.console
        self.logger = None
        self.config_manager = None

    def start_environment(self):
        self.context = AppContextParser.make_context()
        self.config_manager = ConfigManager(self.context.app_name)

        logging.basicConfig(
            filename=self.config_manager.new_log_file(),
            filemode="w",
            level=logging.NOTSET,
            format="%(message)s",
            datefmt="[%X]",
        )
        self.logger = logging.getLogger(self.context.app_name)

        self.progress.start()
        self.whisper(f"{self.context.app_name} started.")
        return self

    def stop_environment(self):
        self.progress.stop()
        self.config_manager.remove_old_log_files()
        self.whisper(f"{self.context.app_name} stopped.")
        return self

    def __enter__(self):
        self.start_environment()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_environment()
        return False

    def say(self, *args):
        self.console.print(*args)
        for arg in args:
            self.logger.info(arg)

    def whisper(self, *args):
        if self.context.debug:
            self.console.log(*args)
        for arg in args:
            self.logger.info(arg)


server = AppServer()
