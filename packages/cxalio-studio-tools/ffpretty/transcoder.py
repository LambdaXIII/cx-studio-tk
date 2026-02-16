import asyncio
import itertools
from pathlib import Path

from cx_studio.ffmpeg import FFmpegAsync, FFmpegArgumentsPreProcessor
from cx_studio.ffmpeg.cx_ff_infos import FFmpegCodingInfo
from cx_tools.app.safe_error import SafeError
from cx_wealth import IndexedListPanel
from .appenv import appenv


class Transcoder:
    def __init__(self, ffmpeg_executable: str | Path | None = None):
        self._ffmpeg = FFmpegAsync(ffmpeg_executable)
        self._taskID = None
        self._task_description = "Transcoding"
        self._ffmpeg_outputs = []

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

    async def _on_verbose(self, line: str):
        """处理FFmpeg输出日志"""
        self._ffmpeg_outputs.append(line)

    async def _random_task_description(
        self, inputs: list[str] | None = None, outputs: list[str] | None = None
    ):
        """随机选择一个任务描述"""
        contents = []
        for x in inputs:
            contents.append(Path(x).name + " ->")
        for x in outputs:
            contents.append("-> " + Path(x).name)
        if not contents:
            contents.append("转码中……")

        for t in itertools.cycle(contents):
            if not self._ffmpeg.is_running():
                break
            self._task_description = t
            await asyncio.sleep(2)

    async def run(self, arguments: list[str] | None = None):
        """执行转码任务

        Args:
            arguments: FFmpeg命令行参数列表

        Returns:
            bool: 转码是否成功
        """
        arguments = arguments or []

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
        non_exist_dirs = filter(
            lambda x: not x.exists(), [Path(a).parent for a in outputs]
        )
        if non_exist_dirs:
            for d in non_exist_dirs:
                d.mkdir(parents=True, exist_ok=True)
            appenv.whisper(IndexedListPanel(non_exist_dirs, title="创建的输出目录"))

        # 统计文件数量用于显示
        m, n = len(inputs), len(outputs)
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

        @self._ffmpeg.on("started")
        def on_started():
            appenv.progress.update(
                self._taskID, description=f"{summary}[cx.success]开始转码...[/]"
            )

        @self._ffmpeg.on("finished")
        def on_finished():
            appenv.progress.update(
                self._taskID, description=f"{summary}[cx.success]转码完成[/]"
            )

        @self._ffmpeg.on("terminated")
        def on_terminated():
            appenv.progress.update(
                self._taskID, description=f"{summary}[cx.error]转码失败[/]"
            )
            appenv.whisper(self._ffmpeg_outputs, title="FFmpeg 输出")

        try:
            main_task = asyncio.create_task(self._ffmpeg.execute(arguments))
            desc_task = asyncio.create_task(
                self._random_task_description(inputs, outputs)
            )
            while not main_task.done():
                await asyncio.sleep(0.1)
                if appenv.really_wanna_quit_event.is_set():
                    appenv.whisper("尝试终止任务……")
                    self._ffmpeg.cancel()
                    await asyncio.sleep(1)
                    break
            result = main_task.result()
            await desc_task

        except asyncio.CancelledError:
            self._ffmpeg.cancel()
            result = False

        except SafeError:
            raise

        except Exception as e:
            appenv.progress.update(
                self._taskID, description=f"{summary}[cx.error]转码异常: {str(e)}[/]"
            )
            result = False
            raise SafeError(f"{str(e)}")
        finally:
            # 清理事件监听器
            self._ffmpeg.remove_all_listeners()

        if not result:
            if self._ffmpeg.is_canceled:
                raise SafeError("[cx.warning]用户取消了操作。[/]")
            else:
                raise SafeError("[cx.error]操作失败，请排查问题。[/]")

        return result
