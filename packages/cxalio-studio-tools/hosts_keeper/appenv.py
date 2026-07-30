import importlib.resources
from . import __version__
from hosts_keeper.i18n import _

from typing import override

from cx_tools.app import IAppEnvironment
from cx_wealthy import rich_types as r


class AppEnv(IAppEnvironment):
    def __init__(self) -> None:
        super().__init__()
        self.app_name = "HostsKeeper"
        self.app_version = __version__

        self.progress = r.Progress(
            r.SpinnerColumn(),
            r.TextColumn(
                "[progress.description]{task.description}",
                table_column=r.Column(ratio=60, no_wrap=True),
            ),
            r.BarColumn(table_column=r.Column(ratio=40)),
            r.TaskProgressColumn(justify="right"),
            r.TimeRemainingColumn(compact=True),
            expand=True,
            console=self.console,
            transient=True,
        )

    @override
    def start(self) -> None:
        self.show_banners()
        super().start()
        self.progress.start()

    @override
    def stop(self) -> None:
        self.progress.refresh()
        self.progress.stop()
        super().stop()

    def show_banners(self) -> None:
        banners = []
        assert __package__ is not None, "AppEnv must be imported as part of a package"
        banner_text = importlib.resources.read_text(
            __package__, "banner.txt", encoding="utf-8"
        )
        banners.append(
            r.Align.center(
                r.Text(banner_text, style="bold cyan", no_wrap=True, overflow="crop")
            )
        )
        banners.append(
            r.Align.center(r.Text(_("你的 hosts 由我来守护！"), style="bold cyan"))
        )
        banners.append(
            r.Align.center(r.Text("v" + self.app_version, style="bold cyan"))
        )
        self.say(r.Group(*banners))


appenv = AppEnv()
