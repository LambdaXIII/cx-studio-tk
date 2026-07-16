import asyncio
import argparse
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from cx_studio.core.cx_time import CxTime

from cx_studio.ffmpeg import FFmpegArgumentsPreProcessor
from cx_studio.filesystem import FileList
from cx_tools.app import IApplication, SafeError
from cx_wealthy import WealthyDetailPanel
from media_killer.media import FileLogType, Mission, MissionResult

from .app_help import AppHelp
from .appenv import appenv
from .mission_maker import MissionMaker
from .mission_runner import MissionRunner


def _run_async(coro) -> MissionResult:
    """在手动 event loop 中运行协程，不覆盖 SIGINT handler。

    使用 ``asyncio.run()`` 时，Python 3.13 会覆盖 SIGINT handler 导致
    我们的 DoubleTrigger/``_cancel_event`` 失效。本函数直接使用
    ``loop.run_until_complete`` 运行，不碰信号 handler，确保 Ctrl+C
    能通过 ``appenv.handle_interrupt`` → ``runner.cancel()`` →
    ``_cancel_event`` 机制干净取消。
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    except asyncio.CancelledError:
        return MissionResult.CANCELED
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def _format_size(size: float) -> str:
    """将字节数转为可读的尺寸字符串。"""
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(size) < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TiB"


class FFPrettyApp(IApplication):
    """FFPretty 应用类 — FFmpeg 的 CLI 前端，提供友好的用户界面。"""

    def __init__(self, arguments: Sequence[str] | None = None):
        """初始化 FFPretty 应用。

        只初始化基本状态，参数解析延迟到 ``_parse_arguments()`` 在 ``run()`` 中调用。
        """
        super().__init__(arguments)
        self._pretending = False
        self._overwrite: bool = False
        self.arguments: list[str] = []
        self._parsed = False
        self._garbage_files = FileList()

    def start(self):
        """启动应用。"""
        appenv.start()
        self.start_time = datetime.now()

    def stop(self):
        """停止应用。由 ``__exit__`` 调用，始终执行。"""
        appenv.stop()
        elapsed = datetime.now() - self.start_time
        if elapsed.total_seconds() > 1:
            appenv.say(
                f"执行结束，用时[cx.number]"
                f"{CxTime.from_seconds(elapsed.total_seconds()).pretty_string}[/]。"
            )

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出应用。始终执行 stop()，捕获已知异常类型输出友好提示。"""
        self.stop()
        if exc_type is None:
            pass
        elif issubclass(exc_type, SafeError):
            appenv.say(f"[{exc_val.style}]{exc_val}[/]")
            return True
        elif exc_type is KeyboardInterrupt:
            appenv.say("[cx.warning]用户中断[/]")
            return True
        return False

    # ── 参数解析 ──

    def _parse_arguments(self):
        """使用 argparse 解析 ffpretty 自有参数，剩余参数存入 self.arguments。"""
        if self._parsed:
            return
        self._parsed = True

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-d", "--debug", action="store_true")
        parser.add_argument("--pretend", action="store_true")
        parser.add_argument("-y", "--overwrite", action="store_true")
        parser.add_argument("-n", "--no-overwrite", action="store_true")

        parsed, unknowns = parser.parse_known_args(self.sys_arguments)

        appenv.debug_mode = parsed.debug
        self._pretending = parsed.pretend

        if parsed.overwrite and parsed.no_overwrite:
            raise SafeError("-y/--overwrite 与 -n/--no-overwrite 不可同时使用。")

        self._overwrite = parsed.overwrite
        self.arguments = list(unknowns)

    # ── 转码模式 ──

    def _check_input_exist(self, mission: Mission):
        """校验输入文件存在性。"""
        missing = [f for f in (s.filename for s in mission.inputs) if not f.exists()]
        if missing:
            raise SafeError(
                "输入文件不存在:\n" + "\n".join(f"  - {str(f)}" for f in missing)
            )

    def _on_file_logged(self, log_type: FileLogType, paths: list[Path]) -> None:
        """FILE_LOGGED 处理器：追踪垃圾文件，debug 模式输出操作信息。"""
        if log_type == FileLogType.DEPRECATED:
            for p in paths:
                self._garbage_files.append(p)
                if appenv.debug_mode:
                    appenv.whisper(f"[dim yellow]临时文件: {p}（待清理）[/]")
        elif log_type == FileLogType.SAVED and appenv.debug_mode:
            for p in paths:
                appenv.whisper(f"[dim]输出文件: {p}[/]")

    def _cleanup_garbage(self):
        """清理执行过程中残留的临时文件。"""
        if len(self._garbage_files) == 0:
            return
        count = len(self._garbage_files)
        appenv.say(f"清理 {count} 个残留临时文件...")
        for f in self._garbage_files:
            try:
                f.unlink(missing_ok=True)
            except OSError:
                pass
        self._garbage_files.clear()

    def run_transcode(self):
        """运行转码过程。"""
        ffmpeg_path = appenv.ffmpeg_executable
        if ffmpeg_path is None:
            raise SafeError("当前环境中未找到 [cx.filepath]ffmpeg[/] 可执行文件。")
        maker = MissionMaker(ffmpeg_path)
        mission = maker.make(self.arguments, overwrite=self._overwrite)

        self._check_input_exist(mission)

        if appenv.debug_mode:
            short_id = str(mission.mission_id)[:6]
            appenv.whisper(
                WealthyDetailPanel(
                    mission,
                    title=(f"[bright_black]M[/] [dim green]{short_id}[/]"),
                )
            )

        runner = MissionRunner(
            mission, appenv.progress, appenv, pretending=self._pretending
        )

        runner.set_file_handler(self._on_file_logged)

        appenv._active_runner = runner
        try:
            result = _run_async(runner.run())
        finally:
            appenv._active_runner = None
            self._cleanup_garbage()
        if result is MissionResult.CANCELED:
            appenv.say("[cx.warning]用户中断[/]")
            return

        if result is MissionResult.SKIPPED:
            appenv.progress.stop()
            appenv.say(
                "[cx.error]目标文件已存在，跳过执行。"
                "如需覆盖请添加 [cx.argument]-y[/] 参数。[/]"
            )
            return

        if result is MissionResult.FAILED:
            if runner.status and runner.status.error_tail:
                appenv.say(
                    "[cx.error]FFmpeg 异常退出，错误信息：[/]\n"
                    f"[dim]{runner.status.error_tail}[/]"
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
                appenv.say(
                    f"[cx.info]输入: [cx.number]{_format_size(input_total)}[/]"
                    f"  → 输出: [cx.number]{_format_size(output_total)}[/]"
                    f"  ({'压缩至' if ratio < 0.95 else '膨胀'}"
                    f" [cx.number]{ratio:.1%}[/])[/]"
                )
        except OSError:
            pass

    # ── 探测模式 ──

    def run_probe(self, files: list[Path]) -> None:
        """探测模式：逐文件输出媒体信息。"""
        from .info_elements import MediaInfoDisplay

        for file in files:
            try:
                info = appenv.media_db.get_media_info(file)
            except Exception as e:
                appenv.say(f"[cx.error]探测失败: {file} — {e}[/]")
                continue
            if info is None:
                appenv.say(f"[cx.warning]无法识别媒体文件: {file}[/]")
                continue
            display = MediaInfoDisplay(info)
            appenv.say(display)

    # ── 入口 ──

    def run(self):
        self._parse_arguments()
        if "-h" in self.arguments or "--help" in self.arguments:
            help_info = AppHelp()
            appenv.say(help_info)
            return

        if not self._pretending and not appenv.ffmpeg_executable:
            raise SafeError("当前环境中未找到 [cx.filepath]ffmpeg[/] 可执行文件。")

        if not self.arguments:
            raise SafeError("未提供任何参数。")

        io_processor = FFmpegArgumentsPreProcessor(*self.arguments)
        inputs = list(io_processor.iter_input_files())
        outputs = list(io_processor.iter_output_files())
        options = list(io_processor.iter_option_pairs())

        if (not inputs) and (not outputs):
            raise SafeError(
                "没有提供需要处理的文件，请按照 ffmpeg 的规则制定输入输出文件，"
                "或直接制定需要探测的文件。"
            )

        if len(inputs) > 0 and len(outputs) > 0:
            self.run_transcode()
        elif len(inputs) > 0 or not options:
            self.run_probe([Path(x) for x in inputs + outputs])
        else:
            appenv.say("[cx.error]参数无法解读。")
