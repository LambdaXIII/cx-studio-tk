"""media_killer 应用环境。

继承 IAppEnvironment，提供 media_killer 专用的运行环境：
- 合并自定义主题 (cx.mk.*)
- 初始化 Progress (transient=True)
- 管理 MediaDB 生命周期
- 注册 DoubleTrigger 中断回调
- 实现 banner 显示、garbage 清理、统计输出
"""

from __future__ import annotations

import asyncio
import importlib.resources
import signal
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from cx_studio.core.cx_time import CxTime
from cx_studio.core.cx_filesize import FileSize
from cx_studio.filesystem import FileSizeCounter
from cx_tools.app import ConfigManager, IAppEnvironment
from cx_tools.i18n import _
from cx_wealthy import rich_types as r

from .appcontext import AppContext, OVERWRITE_DANGER, OVERWRITE_SAFE
from .media import MediaDB
from .theme import media_killer_theme


class AppEnv(IAppEnvironment):
    """media_killer 应用环境。

    继承 IAppEnvironment，提供 media_killer 专用的运行环境：
    - 合并自定义主题 (cx.mk.*) 到 Console
    - 初始化 Progress (transient=True, 共用 console)
    - 管理 MediaDB 生命周期 (connect/close)
    - 注册 DoubleTrigger 中断回调
    - 实现 banner 显示、garbage 清理、统计输出

    Attributes:
        context: 命令行参数上下文
        progress: Rich Progress 实例
        config_manager: 配置管理器
        media_db: MediaDB 实例
    """

    def __init__(self) -> None:
        """初始化 AppEnv。

        设置应用元数据、合并自定义主题、初始化 Progress、
        创建 ConfigManager 和 MediaDB 实例。
        """
        super().__init__()

        # 应用元数据
        self.app_name = "MediaKiller"
        self.app_version = "0.9"
        self.app_description = _("媒体文件批量转码工具")

        # 合并自定义主题
        self.console_theme = media_killer_theme
        self.console = r.Console(
            stderr=True,
            theme=self.console_theme,
            highlighter=self.highlighter,
            highlight=False,
        )

        # 命令行参数上下文（延迟初始化）
        self.context: AppContext = AppContext()

        # Progress 初始化（transient=True, 共用 console）
        self.progress = r.Progress(
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

        # 配置管理器
        self.config_manager = ConfigManager(self.app_name)

        # MediaDB 实例（延迟 connect）
        db_path = self.config_manager.get_file("media_info.db")
        self.media_db = MediaDB(db_path=db_path)

        # Garbage 文件集合
        self._garbage_files: set[Path] = set()
        # 文件处理清单
        self.processed_files: set[Path] = set()
        self.generated_files: set[Path] = set()

        # 应用启动时间
        self._app_start_time: datetime

        # 文件大小统计
        self.input_filesize_counter = FileSizeCounter()
        self.output_filesize_counter = FileSizeCounter()

    def is_debug_mode_on(self) -> bool:
        """返回是否处于 debug 模式。

        Returns:
            True 若 context.debug_mode 为 True
        """
        return self.context.debug_mode

    def load_arguments(self, arguments: Sequence[str] | None = None) -> None:
        """从命令行参数加载上下文。

        Args:
            arguments: 命令行参数列表（不含程序名）
        """
        self.context = AppContext.from_arguments(list(arguments or []))

    def start(self) -> None:
        """启动应用环境。

        调用 super().start()，启动 Progress，连接 MediaDB，
        记录启动时间。
        """
        super().start()
        self.progress.start()
        self.media_db.connect()
        self._app_start_time = datetime.now()

    def stop(self) -> None:
        """停止应用环境。

        停止 Progress，关闭 MediaDB，清理 garbage 文件，
        输出文件大小统计和耗时统计。
        """
        # 停止 Progress
        self.progress.refresh()
        time.sleep(0.1)
        self.progress.stop()

        # 关闭 MediaDB
        self.media_db.close()

        # 清理 garbage 文件
        self.clean_garbage_files()

        # 清理旧日志文件
        self.config_manager.remove_old_log_files()

        # 输出文件大小统计
        input_size = self.input_filesize_counter.total_size
        output_size = self.output_filesize_counter.total_size
        size_report = ""
        if input_size.total_bytes > 0:
            size_report += f"[dim]{_('输入文件总大小:')} [cx.number]{FileSize.from_bytes(input_size.total_bytes).pretty_string}[/]"
        if output_size.total_bytes > 0:
            if size_report:
                size_report += "  "
            size_report += f"[dim]{_('输出文件总大小:')} [cx.number]{FileSize.from_bytes(output_size.total_bytes).pretty_string}[/]"
        if size_report:
            self.say(size_report)

        # 输出耗时统计（超过 5 秒）
        time_spent = datetime.now() - self._app_start_time
        if time_spent.total_seconds() > 5:
            self.say(
                _("总共耗时 {time_str}。").format(
                    time_str=CxTime.from_seconds(
                        time_spent.total_seconds()
                    ).pretty_string
                )
            )

        super().stop()

    def show_banner(self) -> None:
        """显示应用 banner。

        读取 banner.txt 资源文件，显示工具名、版本号、
        应用描述和当前模式标签。
        """
        banners = []

        # 读取 banner.txt
        with importlib.resources.open_text("media_killer", "banner.txt") as f:
            banner_text = r.Text(
                f.read(),
                style="cx.mk.banner",
                no_wrap=True,
                overflow="crop",
                justify="center",
            )
            banners.append(r.Align.center(banner_text))

        # 工具名 + 版本号
        version_info = r.Text.from_markup(
            f"[cx.info]{self.app_name}[/] [cx.number]v{self.app_version}[/]"
        )
        banners.append(r.Align.center(version_info))

        # 应用描述或模式标签
        description = r.Text(self.app_description, style="bright_black")
        tags = []
        if self.context.pretending_mode:
            tags.append(f"[cx.mk.mode.simulate]{_('模拟运行')}[/]")
        mode = self.context.overwrite_mode
        if mode == OVERWRITE_SAFE:
            tags.append(
                f"[cx.mk.mode.no_overwrite]{_('安全模式启动，将拒绝任何覆盖操作')}[/]"
            )
        elif mode == OVERWRITE_DANGER:
            tags.append(
                f"[cx.mk.mode.overwrite]{_('覆盖模式已启动，将自动覆盖任何输出')}[/]"
            )
        if tags:
            description = r.Text.from_markup(" · ".join(tags))
        banners.append(r.Align.center(description))

        self.say(r.Group(*banners))

    def add_garbage_files(self, *filenames: str | Path) -> None:
        """添加 garbage 文件。

        Args:
            filenames: 文件路径列表
        """
        for f in filenames:
            self._garbage_files.add(Path(f))

    def clean_garbage_files(self) -> None:
        """清理 garbage 文件。

        删除所有已登记的 garbage 文件，输出清理统计。
        Windows 上已终止的 ffmpeg 进程可能尚未完全释放文件句柄，
        遇到 PermissionError 时最多重试 3 次（间隔 0.5 秒），
        仍失败则跳过该文件并输出警告。
        """
        if not self._garbage_files:
            return

        self.say(f"[dim]{_('正在清理失败的目标文件...')}[/]")
        for filename in self._garbage_files:
            self.whisper(f"[dim]{_('删除垃圾文件')}[/] [cx.filepath]{filename}[/]")
            self._unlink_with_retry(filename)

        self.say(
            _("已清理 {count} 个失败的垃圾文件。").format(
                count=len(self._garbage_files)
            )
        )
        self._garbage_files.clear()

    @staticmethod
    def _unlink_with_retry(
        filename: Path, max_retries: int = 3, delay: float = 0.5
    ) -> None:
        """删除文件，遇 PermissionError 重试。

        Args:
            filename: 要删除的文件路径
            max_retries: 最大重试次数
            delay: 重试间隔（秒）
        """
        for attempt in range(max_retries):
            try:
                filename.unlink(missing_ok=True)
                return
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    appenv.say(
                        f"[cx.warning]{_('无法删除文件（可能仍被占用）: {path}').format(path=filename)}[/]"
                    )
            except OSError:
                # 其他文件系统错误也跳过，不阻塞清理流程
                break

    def pretending_sleep(self, interval: float = 0.2) -> None:
        """模拟运行模式下的同步睡眠。

        若处于假装模式，睡眠指定时间。

        Args:
            interval: 睡眠秒数
        """
        if self.context.pretending_mode:
            time.sleep(interval)

    async def pretending_asleep(self, interval: float = 0.2) -> None:
        """模拟运行模式下的异步睡眠。

        若处于假装模式，异步睡眠指定时间。

        Args:
            interval: 睡眠秒数
        """
        if self.context.pretending_mode:
            await asyncio.sleep(interval)


# 全局单例
appenv = AppEnv()

# 注册 SIGINT 处理器
signal.signal(signal.SIGINT, appenv.handle_interrupt)
