"""media_killer 应用环境。

继承 IAppEnvironment，提供 media_killer 专用的运行环境：
- 合并自定义主题 (cx.mk.*)
- 初始化 Progress (transient=True)
- 管理 MediaDB 生命周期
- 注册 DoubleTrigger 中断回调
- 实现 banner 显示、garbage 清理、统计输出
"""

from __future__ import annotations

from . import __version__

import asyncio
import importlib.resources
import signal
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from cx_studio.core.cx_time import CxTime
from cx_studio.filesystem import FileList
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
        self.app_version = __version__
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

        # 文件列表（FileList 自动去重 + 延迟大小计算）
        # sizer 通过 MediaDB.FileBytesGetter 从缓存拉取文件大小
        sizer = self.media_db.make_file_bytes_getter()
        self.garbage_files = FileList(sizer_function=sizer)
        self.processed_files = FileList(sizer_function=sizer)
        self.generated_files = FileList(sizer_function=sizer)

        # 应用启动时间
        self._app_start_time: datetime

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

        停止 Progress，执行文件统计与清理（cleanup），
        清理旧日志，关闭 MediaDB，输出耗时统计。
        """
        # 停止 Progress
        self.progress.refresh()
        time.sleep(0.1)
        self.progress.stop()

        # 文件统计与 garbage 清理（依赖 MediaDB 连接）
        self.cleanup()

        # 清理旧日志文件
        self.config_manager.remove_old_log_files()

        # 关闭 MediaDB
        self.media_db.close()

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
            self.garbage_files.append(Path(f))

    def cleanup(self) -> None:
        """退出阶段统一扫尾清理。

        先输出 processed/generated 两个列表的统计报告（计数 + 大小），
        再清理 garbage_files 中的垃圾文件并输出清理报告。
        所有报告使用自然语言，数值为 0 时不提示该部分。
        """
        # --- I/O 列表统计报告 ---
        self._report_file_list(self.processed_files, _("本次执行处理了 {n} 个文件"))
        self._report_file_list(self.generated_files, _("本次执行生成了 {n} 个文件"))

        # --- garbage 清理 ---
        if len(self.garbage_files) > 0:
            self.say(f"[cx.error]{_('正在清理失败的目标文件...')}[/]")
            for filename in self.garbage_files:
                self.whisper(f"[cx.filepath]{filename}[/]")
                self._unlink_with_retry(filename)
            self.say(
                f"[cx.error]{_('清理了 {n} 个失败的目标文件').format(n=len(self.garbage_files))}[/]"
            )
            self.garbage_files.clear()

    def _report_file_list(self, file_list: FileList, msgid: str) -> None:
        """输出单个文件列表的统计报告（一行）。

        文件数为 0 时整句不输出。文件数 > 0 但总大小为 0 时
        仅输出计数句，不带括号大小部分。文件数和大小均 > 0 时
        输出 '文案（大小）' 格式。

        Args:
            file_list: 要报告的 FileList
            msgid: 带 {n} 占位符的中文 msgid，如 "本次执行处理了 {n} 个文件"
        """
        count = len(file_list)
        if count == 0:
            return
        text = f"[cx.info]{_(msgid).format(n=count)}[/]"
        total = file_list.total_size
        if total.total_bytes > 0:
            text += f"（[cx.number]{total.pretty_string}[/]）"
        self.say(text)

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
