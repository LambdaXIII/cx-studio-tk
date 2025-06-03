import asyncio
from datetime import datetime
import importlib
import importlib.resources
import signal
import time
from collections.abc import Sequence
from pathlib import Path

from cx_studio.core.cx_filesize import FileSize
from cx_studio.core.cx_time import CxTime
from cx_tools.app import IAppEnvironment, ConfigManager
from cx_wealth import rich_types as r
from media_killer.components.exception import SafeError
from .appcontext import AppContext

# from .mk_help_info import MKHelp
from cx_tools import FileSizeCounter


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "MediaKiller"
        self.app_version = "0.5.0.4"
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
        self._app_start_time: datetime

        self.input_filesize_counter = FileSizeCounter()
        self.output_filesize_counter = FileSizeCounter()

    def is_debug_mode_on(self):
        return self.context.debug_mode

    def load_arguments(self, arguments: Sequence[str] | None = None):
        self.context = AppContext.from_arguments(arguments)

    def start(self):
        self.progress.start()
        self._app_start_time = datetime.now()

    def stop(self):
        self.progress.refresh()
        time.sleep(0.1)
        self.progress.stop()
        self.clean_garbage_files()
        self.config_manager.remove_old_log_files()

        input_filesize = self.input_filesize_counter.total_size
        output_filesize = self.output_filesize_counter.total_size
        filesize_report = ""
        if input_filesize.total_bytes > 0:
            filesize_report = (
                f"[dim]输入文件总大小: [blue]{input_filesize.pretty_string}[/]"
            )
        if output_filesize.total_bytes > 0:
            filesize_report += (
                f"[dim] 输出文件总大小: [blue]{output_filesize.pretty_string}[/]"
            )
        if len(filesize_report) > 0:
            self.say(filesize_report)

        time_spent = datetime.now() - self._app_start_time
        if time_spent.total_seconds() > 5:
            self.say(
                "[dim]总共耗时[blue]{}[/]。[/]".format(
                    CxTime.from_seconds(time_spent.total_seconds()).pretty_string
                )
            )

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


appenv = AppEnv()


signal.signal(signal.SIGINT, appenv.handle_interrupt)
