import logging
from argparse import ArgumentParser

from rich.progress import Progress

from common import ConfigManager
from mediakiller.appcontext import AppContext


class AppServer:
    def __init__(self):
        self.context = None
        self.progress = Progress()
        self.console = self.progress.console
        self.logger = None
        self.config_manager = None

    @staticmethod
    def parse_arguments() -> AppContext:
        parser = ArgumentParser()
        parser.add_argument(
            "--tutorial", action="store_true", help="Show full tutorial."
        )
        parser.add_argument(
            "-g", "--generate", action="store_true", help="Generate script file."
        )
        parser.add_argument("--save-script", "-s", help="Generate script file")
        parser.add_argument(
            "--sort",
            choices=["source", "preset", "target", "x"],
            default="x",
            help="Set sorting mode",
        )

        parser.add_argument(
            "--continue",
            action="store_true",
            help="Continue last task.",
            dest="continue_mode",
        )
        parser.add_argument(
            "--pretend", action="store_true", help="Pretend to execute task."
        )
        parser.add_argument("--debug", action="store_true", help="Start debug mode.")
        parser.add_argument("sources", nargs="*", help="Sources to process")

        result = AppContext()
        args = parser.parse_args()
        result.presets = [p for p in args.sources if p.endswith(".toml")]
        result.sources = [s for s in args.sources if not s.endswith(".toml")]
        result.script_output = args.save_script
        result.pretending_mode = args.pretend
        result.debug = args.debug
        result.sort_mode = args.sort
        result.continue_mode = args.continue_mode
        return result

    def start_environment(self):
        self.context = self.parse_arguments()
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
