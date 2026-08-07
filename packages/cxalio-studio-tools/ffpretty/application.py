import asyncio
from datetime import datetime
from pathlib import Path

from cx_studio.core.cx_time import CxTime
from cx_studio.ffmpeg import FFmpegArgumentsPreProcessor
from cx_studio.filesystem import FileList
from cx_tools.app import IApplication, IAppEnvironment, SafeError, run_async
from cx_wealthy import WealthyDetailPanel, rich_types as r
from ffpretty.i18n import _

from .common import FileLogType, MediaDB, Mission, MissionResult

from .app_help import FFPrettyHelp
from .appcontext import FFPrettyContext
from .components.mission_maker import MissionMaker
from .components.mission_runner import MissionRunner


def _format_size(size: float) -> str:
    """将字节数转为可读的尺寸字符串。"""
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(size) < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TiB"


class FFPrettyApp(IApplication):
    """FFPretty 应用类 — FFmpeg 的 CLI 前端，提供友好的用户界面。

    通过构造参数注入 appenv、context、progress，不绑定特定 appenv 单例。
    """

    def __init__(
        self, appenv: IAppEnvironment, context: FFPrettyContext, progress: r.Progress
    ):
        """初始化 FFPretty 应用。

        Args:
            appenv: 应用环境（IAppEnvironment）。
            context: 命令行上下文（FFPrettyContext）。
            progress: 可选的 Rich Progress 实例。
        """
        super().__init__(appenv, context)
        self.context = context
        self.progress = progress
        self._pretending = self.context.pretending_mode
        self._overwrite = self.context.overwrite
        self._garbage_files = FileList()
        self._active_runner: MissionRunner | None = None
        self._media_db = MediaDB()

    def start(self):
        """启动应用。"""
        self.appenv.set_debug_mode(self.context.debug_mode)
        self._media_db.connect()
        self.start_time = datetime.now()

        from cx_studio.clikit import SECOND_TRIGGERED

        @self.appenv.interrupt_handler.on(SECOND_TRIGGERED)
        def __cancel_runner():
            if self._active_runner is not None:
                self._active_runner.cancel()

    def stop(self):
        """停止应用。由 ``__exit__`` 调用，始终执行。"""
        self._media_db.close()
        elapsed = datetime.now() - self.start_time
        if elapsed.total_seconds() > 1:
            self.appenv.say(
                f"{_('执行结束，用时')}[cx.number]"
                f"{CxTime.from_seconds(elapsed.total_seconds()).pretty_string}[/]{_('。')}"
            )

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出应用。始终执行 stop()，捕获已知异常类型输出友好提示。"""
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is not None and issubclass(exc_type, SafeError):
            self.appenv.say(f"[{exc_val.style}]{exc_val}[/]")
            result = True
        elif exc_type is KeyboardInterrupt:
            self.appenv.say(f"[cx.warning]{_('用户中断')}[/]")
            result = True
        return result

    # ── 转码模式 ──

    def _check_input_exist(self, mission: Mission):
        """校验输入文件存在性。"""
        missing = [f for f in (s.filename for s in mission.inputs) if not f.exists()]
        if missing:
            raise SafeError(
                _("输入文件不存在:")
                + "\n"
                + "\n".join(f"  - {str(f)}" for f in missing)
            )

    def _on_file_logged(self, log_type: FileLogType, paths: list[Path]) -> None:
        """FILE_LOGGED 处理器：追踪垃圾文件，debug 模式输出操作信息。"""
        if log_type == FileLogType.DEPRECATED:
            for p in paths:
                self._garbage_files.append(p)
                if self.context.debug_mode:
                    self.appenv.whisper(
                        f"[dim yellow]{_('临时文件: {path}（待清理）').format(path=p)}[/]"
                    )
        elif log_type == FileLogType.SAVED and self.context.debug_mode:
            for p in paths:
                self.appenv.whisper(f"[dim]{_('输出文件: {path}').format(path=p)}[/]")

    def _cleanup_garbage(self):
        """清理执行过程中残留的临时文件。"""
        if len(self._garbage_files) == 0:
            return
        count = len(self._garbage_files)
        self.appenv.say(_("清理 {count} 个残留临时文件...").format(count=count))
        for f in self._garbage_files:
            try:
                f.unlink(missing_ok=True)
            except OSError:
                pass
        self._garbage_files.clear()

    def run_transcode(self):
        """运行转码过程。"""
        ffmpeg_path = self.context.ffmpeg_executable
        if ffmpeg_path is None:
            raise SafeError(
                f"{_('当前环境中未找到')} [cx.filepath]ffmpeg[/] {_('可执行文件。')}"
            )
        maker = MissionMaker(ffmpeg_path)
        mission = maker.make(self.context.arguments, overwrite=self._overwrite)

        self._check_input_exist(mission)

        if self.context.debug_mode:
            short_id = str(mission.mission_id)[:6]
            self.appenv.whisper(
                WealthyDetailPanel(
                    mission,
                    title=(f"[bright_black]M[/] [dim green]{short_id}[/]"),
                )
            )

        assert self.progress is not None, "progress 不应为 None"
        runner = MissionRunner(
            mission, self.progress, self.appenv, pretending=self._pretending
        )

        runner.set_file_handler(self._on_file_logged)

        self._active_runner = runner
        try:
            try:
                result = run_async(runner.run())
            except asyncio.CancelledError:
                result = MissionResult.CANCELED
        finally:
            self._active_runner = None
            self._cleanup_garbage()
        if result is MissionResult.CANCELED:
            self.appenv.say(f"[cx.warning]{_('用户中断')}[/]")
            return
        if result is MissionResult.SKIPPED:
            if self.progress is not None:
                self.progress.stop()
            self.appenv.say(
                f"[cx.error]{_('目标文件已存在，跳过执行。如需覆盖请添加')} "
                f"[cx.argument]-y[/] {_('参数。')}[/]"
            )
            return

        if result is MissionResult.FAILED:
            if runner.failure_info is not None:
                title = (
                    _("FFmpeg 异常退出")
                    if runner.failure_info.is_ffmpeg_failure
                    else _("任务失败")
                )
                self.appenv.say(
                    WealthyDetailPanel(
                        runner.failure_info,
                        title=f"[cx.error]{title}[/]",
                    )
                )
            return

        # ── 成功（SUCCESS）──
        try:
            input_total = sum(
                s.filename.stat().st_size for s in mission.inputs if s.filename.exists()
            )
            output_total = sum(
                s.filename.stat().st_size
                for s in mission.outputs
                if s.filename.exists()
            )
            if input_total > 0 and output_total > 0:
                ratio = output_total / input_total
                self.appenv.say(
                    f"[cx.info]{_('输入')}: [cx.number]{_format_size(input_total)}[/]"
                    f"  → {_('输出')}: [cx.number]{_format_size(output_total)}[/]"
                    f"  ({_('压缩至') if ratio < 0.95 else _('膨胀')}"
                    f" [cx.number]{ratio:.1%}[/])[/]"
                )
        except OSError:
            pass

    # ── 探测模式 ──

    def run_probe(self, files: list[Path]) -> None:
        """探测模式：逐文件输出媒体信息。"""
        from .components.info_elements import MediaInfoDisplay

        for file in files:
            try:
                info = self._media_db.get_media_info(file)
            except Exception as e:
                self.appenv.say(
                    f"[cx.error]{_('探测失败: {path} — {error}').format(path=file, error=e)}[/]"
                )
                continue
            if info is None:
                self.appenv.say(
                    f"[cx.warning]{_('无法识别媒体文件: {path}').format(path=file)}[/]"
                )
                continue
            display = MediaInfoDisplay(info)
            self.appenv.say(display)

    # ── 入口 ──

    def run(self):
        if "-h" in self.context.arguments or "--help" in self.context.arguments:
            help_component = FFPrettyHelp(self.appenv, self.context)
            self.appenv.say(help_component)
            return

        if not self._pretending and not self.context.ffmpeg_executable:
            raise SafeError(
                f"{_('当前环境中未找到')} [cx.filepath]ffmpeg[/] {_('可执行文件。')}"
            )

        if not self.context.arguments:
            raise SafeError(_("未提供任何参数。"))

        io_processor = FFmpegArgumentsPreProcessor(*self.context.arguments)
        inputs = list(io_processor.iter_input_files())
        outputs = list(io_processor.iter_output_files())
        options = list(io_processor.iter_option_pairs())

        if (not inputs) and (not outputs):
            raise SafeError(
                _(
                    "没有提供需要处理的文件，请按照 ffmpeg 的规则制定输入输出文件，"
                    "或直接制定需要探测的文件。"
                )
            )

        if len(inputs) > 0 and len(outputs) > 0:
            self.run_transcode()
        elif len(inputs) > 0 or not options:
            self.run_probe([Path(x) for x in inputs + outputs])
        else:
            self.appenv.say(f"[cx.error]{_('参数无法解读。')}")
