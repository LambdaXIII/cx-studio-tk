import asyncio
import importlib
import importlib.resources
import signal
import time
from collections.abc import Sequence
from pathlib import Path

from cx_tools_common.app_interface import IAppEnvironment, ConfigManager
from cx_wealth import rich_types as r
from media_killer.components.exception import SafeError
from .appcontext import AppContext
from .mk_help_info import MKHelpInfo


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "MediaKiller"
        self.app_version = "0.5.0"
        self.app_description = "媒体文件批量操作工具"
        self.context: AppContext = AppContext()
        self.progress = r.Progress(
            # RenderableColumn("[bright_black]M[/]"),
            r.SpinnerColumn(),
            r.TextColumn(
                "[progress.description]{task.description}",
                table_column=r.Column(ratio=60, no_wrap=True),
            ),
            r.BarColumn(table_column=r.Column(ratio=40)),
            r.TaskProgressColumn(justify="right"),
            r.TimeRemainingColumn(compact=True),
            expand=True,
        )

        self.console = self.progress.console
        self.config_manager = ConfigManager(self.app_name)
        self._garbage_files = []

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
        self.clean_garbage_files()
        self.config_manager.remove_old_log_files()

    def pretending_sleep(self, interval: float = 0.2):
        if self.context.pretending_mode:
            time.sleep(interval)

    async def pretending_asleep(self, interval: float = 0.2):
        if self.context.pretending_mode:
            await asyncio.sleep(interval)

    def add_garbage_files(self, *filenames: str | Path):
        self._garbage_files.extend(map(Path, filenames))

    def clean_garbage_files(self):
        if not self._garbage_files:
            return
        self.say("[dim]正在清理失败的目标文件...[/]")
        for filename in self._garbage_files:
            filename.unlink(missing_ok=True)
            self.whisper(f"  {filename} [red]已删除[/red]")
            if self.context.debug_mode:
                time.sleep(0.1)
        self._garbage_files.clear()

    def show_banner(self):
        banners = []

        with importlib.resources.open_text("media_killer", "banner.txt") as banner:
            banner_text = r.Text(
                banner.read(),
                style="bold red",
                no_wrap=True,
                overflow="crop",
                justify="center",
            )
            banners.append(r.Align.center(banner_text))

        version_info = r.Text.from_markup(
            f"[bold blue]{self.app_name}[/] [yellow]v{self.app_version}[/]"
        )
        banners.append(r.Align.center(version_info))

        description = r.Text(self.app_description, style="bright_black")
        tags = []
        if self.context.pretending_mode:
            tags.append("[blue]模拟运行[/]")
        if self.context.force_no_overwrite:
            tags.append("[green]安全模式[/]")
        elif self.context.force_overwrite:
            tags.append("[red]强制覆盖模式[/]")
        if tags:
            description = "·".join(tags)
        banners.append(r.Align.center(description))

        self.say(r.Group(*banners))

    def check_overwritable_file(self, filename: Path, check_only: bool = False) -> bool:
        existed = filename.exists()
        result = not existed
        if self.context.force_overwrite:
            result = True
        if self.context.force_no_overwrite:
            result = False

        if not check_only and not result:
            msg = f"文件 {filename} 已存在，"
            if self.context.force_no_overwrite:
                msg += "请取消 --force-no-overwrite 选项"
            elif not self.context.force_overwrite:
                msg += "请使用 --force-overwrite 选项尝试覆盖"
            msg += "或指定其它文件名."
            raise SafeError(msg)

        if not check_only and result:
            self.say(f"[dim red]文件 {filename} 已存在，将强制覆盖。[/]")
        return result

    def show_help(self):
        self.say(MKHelpInfo())
        return

    def show_full_help(self):
        with importlib.resources.open_text("media_killer", "help.md") as h:
            tuto = h.read()
        tutorial = r.Panel(
            r.Markdown(tuto, style="default"), width=90, style="bright_black"
        )
        self.say(r.NewLine(3))
        self.say(r.Align.center(tutorial))


appenv = AppEnv()


signal.signal(signal.SIGINT, appenv.handle_interrupt)
