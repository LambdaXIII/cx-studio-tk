from cx_tools.app import IAppEnvironment
from rich.console import Console
from .arg_parser import AppContext


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "MediaScout"
        self.app_version = "0.7.0"
        self.output_console = Console()
        self.context: AppContext

    def print(self, *args, **kwargs):
        self.output_console.print(*args, **kwargs)

    def start(self):
        self.context = AppContext.load()

    def stop(self):
        pass

    def is_debug_mode_on(self):
        return self.context.debug_mode

    def show_banner(self):
        self.say("[blue]{}[/] [yellow]v{}[/]".format(self.app_name, self.app_version))


appenv = AppEnv()
