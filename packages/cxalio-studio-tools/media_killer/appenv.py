import asyncio
import importlib.resources
import signal
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from cx_tools import FileSizeCounter
from cx_tools.app import IAppEnvironment, ConfigManager
from cx_tools.i18n import _
from cx_studio.core.cx_time import CxTime
from cx_wealth import rich_types as r
from media_killer.components.exception import SafeError
from .appcontext import AppContext


class AppEnv(IAppEnvironment):
    def __init__(self) -> None:
        super().__init__()
        self.app_name = "MediaKiller"
        self.app_version = "0.7.0"
        self.app_description = _("媒体文件批量操作工具")
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
            console=self.console,
            transient=True,
            expand=True,
        )

        # self.console = self.progress.console
        self.config_manager = ConfigManager(self.app_name)
        self._garbage_files = []
        self._app_start_time: datetime

        self.input_filesize_counter = FileSizeCounter()
        self.output_filesize_counter = FileSizeCounter()

    def is_debug_mode_on(self) -> bool:
        return self.context.debug_mode

    def load_arguments(self, arguments: Sequence[str] | None = None):
        self.context = AppContext.from_arguments(arguments)

    def start(self) -> None:
        self.progress.start()
        self._app_start_time = datetime.now()

    def stop(self) -> None:
        self.progress.refresh()
        time.sleep(0.1)
        self.progress.stop()
        self.clean_garbage_files()
        self.config_manager.remove_old_log_files()

        input_filesize = self.input_filesize_counter.total_size
        output_filesize = self.output_filesize_counter.total_size
        filesize_report = ""
        if input_filesize.total_bytes > 0:
            filesize_report = f"[dim]{_('输入文件总大小:')} [cx.nummber]{input_filesize.pretty_string}[/]"
        if output_filesize.total_bytes > 0:
            filesize_report += f"[dim] {_('输出文件总大小:')} [cx.number]{output_filesize.pretty_string}[/]"
        if len(filesize_report) > 0:
            self.say(filesize_report)

        time_spent = datetime.now() - self._app_start_time
        if time_spent.total_seconds() > 5:
            self.say(
                _("总共耗时{time_str}。").format(
                    time_str=CxTime.from_seconds(
                        time_spent.total_seconds()
                    ).pretty_string
                )
            )

    def pretending_sleep(self, interval: float = 0.2) -> None:
        if self.context.pretending_mode:
            time.sleep(interval)

    async def pretending_asleep(self, interval: float = 0.2) -> None:
        if self.context.pretending_mode:
            await asyncio.sleep(interval)

    def add_garbage_files(self, *filenames: str | Path) -> None:
        self._garbage_files.extend(map(Path, filenames))

    def clean_garbage_files(self) -> None:
        if not self._garbage_files:
            return
        self.say(f"[dim]{_('正在清理失败的目标文件...')}[/]")
        for filename in self._garbage_files:
            filename.unlink(missing_ok=True)
            self.whisper(f"  [cx.filepath]{filename}[/] [red]{_('已删除')}[/red]")
            if self.context.debug_mode:
                time.sleep(0.1)
        self.say(
            _("已清理 {count} 个目标文件。").format(count=len(self._garbage_files))
        )
        self._garbage_files.clear()

    def show_banner(self) -> None:
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
            tags.append(f"[blue]{_('模拟运行')}[/]")
        if self.context.force_no_overwrite:
            tags.append(f"[green1]{_('安全模式')}[/]")
        elif self.context.force_overwrite:
            tags.append(f"[red]{_('强制覆盖模式')}[/]")
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
            if self.context.force_no_overwrite:
                raise SafeError(
                    _(
                        "文件 {name} 已存在，请取消 --force-no-overwrite 选项或指定其它文件名。"
                    ).format(name=filename)
                )
            elif not self.context.force_overwrite:
                raise SafeError(
                    _(
                        "文件 {name} 已存在，请使用 --force-overwrite 选项尝试覆盖或指定其它文件名。"
                    ).format(name=filename)
                )
            raise SafeError(
                _("文件 {name} 已存在，或指定其它文件名。").format(name=filename)
            )

        if not check_only and result:
            self.say(
                f"[dim red]{_('文件 {name} 已存在，将强制覆盖。').format(name=filename)}[/]"
            )
        return result


appenv = AppEnv()


signal.signal(signal.SIGINT, appenv.handle_interrupt)
