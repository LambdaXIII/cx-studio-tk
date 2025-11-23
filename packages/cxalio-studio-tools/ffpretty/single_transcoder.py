from pathlib import Path
import asyncio
from collections.abc import Iterable

from cx_studio.ffmpeg import FFmpegAsync, FFmpegArgumentsPreProcessor
from cx_studio.ffmpeg.cx_ff_infos import FFmpegCodingInfo
from .appenv import appenv
from cx_wealth import IndexedListPanel


class SingleTranscoder:
    def __init__(self, ffmpeg_executable: str | Path | None = None):
        self._ffmpeg = FFmpegAsync(ffmpeg_executable)
        self._taskID = None
        self._task_description = "Transcoding"
        self._ffmpeg_outputs = []
        self._cancel_event = asyncio.Event()

    def __enter__(self):
        self._taskID = appenv.progress.add_task(
            description="[green]准备中...[/]", total=None
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._taskID is not None:
            appenv.progress.remove_task(self._taskID)
            self._taskID = None
        return False

    def cancel(self):
        """取消转码任务"""
        self._cancel_event.set()

    def _get_input_files(self, arguments: Iterable[str]) -> list[str]:
        """从参数中提取输入文件列表"""
        input_files = []
        input_marked = False
        for a in arguments:
            if a == "-i":
                input_marked = True
            elif input_marked:
                input_files.append(a)
                input_marked = False
        return input_files

    def _get_output_files(self, arguments: Iterable[str]) -> list[str]:
        """从参数中提取输出文件列表"""
        output_files = []
        prev_key = None
        for a in arguments:
            if a.startswith("-"):
                prev_key = a
                continue

            if "." in a and prev_key != "-i":
                output_files.append(a)
        return output_files

    async def _on_verbose(self, line: str):
        """处理FFmpeg输出日志"""
        self._ffmpeg_outputs.append(line)

    async def _monitor_progress(self):
        """监控转码进度并更新UI"""
        while not self._cancel_event.is_set():
            await asyncio.sleep(0.1)

    async def run(self, arguments: list[str] | None = None):
        """执行转码任务

        Args:
            arguments: FFmpeg命令行参数列表

        Returns:
            bool: 转码是否成功
        """
        arguments = arguments or []

        # 提取输入输出文件
        input_files = self._get_input_files(arguments)
        output_files = self._get_output_files(arguments)

        # 统计文件数量用于显示
        m, n = len(input_files), len(output_files)
        summary = f"[blue][{m}->{n}][/]"

        # 设置状态更新监听器
        @self._ffmpeg.on("status_updated")
        def on_status_updated(status: FFmpegCodingInfo):
            current = status.current_time.total_seconds
            total = status.total_time.total_seconds if status.total_time else None

            # 格式化速度显示
            speed = "[bright_black][{:.2f}x][/]".format(status.current_speed)

            # 更新进度描述
            appenv.progress.update(
                self._taskID,
                completed=current,
                total=total,
                description=f"{summary}{speed}[green]{self._task_description}[/]",
            )

        # 设置其他事件监听器
        @self._ffmpeg.on("verbose")
        def on_verbose(line: str):
            asyncio.create_task(self._on_verbose(line))

        @self._ffmpeg.on("started")
        def on_started():
            appenv.progress.update(
                self._taskID, description=f"{summary}[green]开始转码...[/]"
            )

        @self._ffmpeg.on("finished")
        def on_finished():
            appenv.progress.update(
                self._taskID, description=f"{summary}[green]转码完成[/]"
            )

        @self._ffmpeg.on("terminated")
        def on_terminated():
            appenv.progress.update(
                self._taskID, description=f"{summary}[red]转码失败[/]"
            )
            appenv.whisper(self._ffmpeg_outputs, title="FFmpeg 输出")

        try:
            # 创建监控任务
            monitor_task = asyncio.create_task(self._monitor_progress())

            # 执行FFmpeg任务
            result = await self._ffmpeg.execute(arguments)

            # 取消监控任务
            monitor_task.cancel()

        except Exception as e:
            appenv.progress.update(
                self._taskID, description=f"{summary}[red]转码异常: {str(e)}[/]"
            )
            raise
        finally:
            # 清理事件监听器
            self._ffmpeg.remove_all_listeners()

        if not result:
            if self.ffmpeg.is_canceled:
                raise SafeError("[cx.warning]用户取消了操作。[/]")
            else:
                raise SafeError("[cx.error]操作失败，请排查问题。[/]")

        return result


def transcode(ffmpeg_executable: str, arguments: list[str] | None = None):
    """执行转码任务

    Args:
        ffmpeg_executable: FFmpeg可执行文件路径
        arguments: FFmpeg命令行参数列表

    Returns:
        bool: 转码是否成功
    """

    io_processor = FFmpegArgumentsPreProcessor(arguments)
    inputs = list(io_processor.iter_input_files())
    outputs = list(io_processor.iter_output_files())

    # 检查输入文件是否存在
    for i in inputs:
        if not Path(i).exists():
            raise SafeError(f"输入文件 {i} 不存在。")

    # 检查输出文件是否已存在
    existed_outputs = [x for x in outputs if Path(x).exists()]
    if existed_outputs and "-y" not in arguments:
        appenv.whisper(IndexedListPanel(existed_outputs, title="已存在的输出文件"))
        raise SafeError("请使用 -y 参数覆盖已存在的文件。")

    # 创建不存在的输出目录
    non_exist_dirs = filter(lambda x: not x.exists(), [Path(a).parent for a in outputs])
    if non_exist_dirs:
        for d in non_exist_dirs:
            d.mkdir(parents=True, exist_ok=True)
        appenv.whisper(IndexedListPanel(non_exist_dirs, title="创建的输出目录"))

    with SingleTranscoder(ffmpeg_executable) as transcoder:
        return asyncio.run(transcoder.run(arguments))
