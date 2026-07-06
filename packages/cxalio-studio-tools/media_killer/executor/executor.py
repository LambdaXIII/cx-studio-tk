"""MissionExecutor - 单 Mission 执行单元。

给定一个完全解析的 Mission，创建目录、运行 FFmpeg、通过事件报告进度、
支持外部取消，并管理临时文件与 garbage。不依赖 appenv。
"""

import asyncio
import os
from pathlib import Path

from pyee.asyncio import AsyncIOEventEmitter

from cx_studio.ffmpeg import FFmpegAsync
from cx_studio.filesystem import is_executable
from cx_tools.i18n import _

from ..mission import Mission
from . import events as evt
from .result import MissionResult


class MissionExecutor(AsyncIOEventEmitter):
    """单 Mission 执行单元。

    继承 ``AsyncIOEventEmitter``，通过事件向外报告进度与状态。
    使用临时文件机制保证输出原子性：FFmpeg 写入 ``mk2tmp.<target>`` 临时文件，
    成功后原子重命名为目标文件；失败或取消时临时文件保留为 garbage。

    事件（见 :mod:`.events`）：
        started, progress_updated, status_updated,
        finished, failed, canceled, verbose
    """

    _TEMP_PREFIX: str = "mk2tmp."

    def __init__(
        self,
        mission: Mission,
        ffmpeg_executable: str | None = None,
    ) -> None:
        """初始化 MissionExecutor。

        Args:
            mission: 要执行的 Mission
            ffmpeg_executable: ffmpeg 可执行文件路径。若为 None，使用 mission.ffmpeg。
        """
        super().__init__()
        self._mission = mission
        self._ffmpeg_executable = ffmpeg_executable or mission.ffmpeg
        self._garbage_files: set[Path] = set()
        self._cancel_event = asyncio.Event()

    @property
    def garbage_files(self) -> set[Path]:
        """返回需要清理的临时文件集合。"""
        return self._garbage_files

    def cancel(self) -> None:
        """取消执行。"""
        self._cancel_event.set()

    # ------------------------------------------------------------------
    # 公开方法
    # ------------------------------------------------------------------

    async def execute(self) -> MissionResult:
        """执行 Mission。

        流程：校验 → 创建输出目录 → 计算临时文件 → 运行 FFmpeg → 提交或保留 garbage。

        Returns:
            MissionResult: 执行结果（SUCCESS/FAILED/CANCELED）
        """
        # 校验阶段抛异常即 FAILED
        try:
            self._validate()
        except Exception as e:
            self.emit(evt.FAILED, str(e))
            return MissionResult.FAILED

        # 计算临时文件映射：目标路径 → 临时路径
        temp_map: dict[Path, Path] = {}
        for output_spec in self._mission.outputs:
            target = output_spec.filename
            temp = target.parent / f"{self._TEMP_PREFIX}{target.name}"
            temp_map[target] = temp

        # 启动前登记 garbage
        for temp in temp_map.values():
            self._garbage_files.add(temp)

        # 构建参数：替换输出路径为临时路径
        arguments = self._build_arguments(temp_map)

        # 创建 FFmpeg 实例并挂载事件转发
        ffmpeg = FFmpegAsync(self._ffmpeg_executable)
        self._attach_listeners(ffmpeg)

        try:
            main_task = asyncio.create_task(ffmpeg.execute(arguments))

            # 轮询等待，期间检查取消信号
            while not main_task.done():
                if self._cancel_event.is_set():
                    ffmpeg.cancel()
                    await main_task
                    return MissionResult.CANCELED
                await asyncio.sleep(0.1)

            ffmpeg_ok: bool = main_task.result()

        except asyncio.CancelledError:
            ffmpeg.cancel()
            return MissionResult.CANCELED

        except Exception as e:
            self.emit(evt.FAILED, str(e))
            return MissionResult.FAILED

        # 用户取消优先于 FFmpeg 结果
        if self._cancel_event.is_set():
            return MissionResult.CANCELED

        if ffmpeg_ok:
            return self._commit_outputs(temp_map)

        # FFmpeg 异常退出
        self.emit(evt.FAILED, _("FFmpeg 执行失败"))
        return MissionResult.FAILED

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        """执行前校验。校验失败抛出异常。"""
        mission = self._mission

        input_files = {spec.filename for spec in mission.inputs}
        output_files = {spec.filename for spec in mission.outputs}

        # 输入输出重叠
        conflicts = input_files & output_files
        if conflicts:
            raise ValueError(
                _("检测到重叠的输入输出文件: {files}").format(
                    files=", ".join(str(f) for f in conflicts)
                )
            )

        # FFmpeg 可执行性
        if not is_executable(Path(self._ffmpeg_executable)):
            raise ValueError(
                _("FFmpeg 可执行文件无效: {path}").format(path=self._ffmpeg_executable)
            )

        # 输入文件存在性
        missing = {f for f in input_files if not f.exists()}
        if missing:
            raise ValueError(
                _("输入文件不存在: {files}").format(
                    files=", ".join(str(f) for f in missing)
                )
            )

        # 输出目录：已存在的必须有写权限
        output_dirs = {f.parent for f in output_files}
        existing_dirs = {d for d in output_dirs if d.exists()}
        invalid_dirs = {d for d in existing_dirs if not os.access(d, os.W_OK)}
        if invalid_dirs:
            raise ValueError(
                _("输出目录无写权限: {dirs}").format(
                    dirs=", ".join(str(d) for d in invalid_dirs)
                )
            )

        # 输出目录：不存在的创建
        new_dirs = {d for d in output_dirs if not d.exists()}
        for d in new_dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _build_arguments(self, temp_map: dict[Path, Path]) -> list[str]:
        """构建 FFmpeg 参数列表，将输出路径替换为临时路径。"""
        result: list[str] = []
        for arg in self._mission.iter_arguments():
            path = Path(arg)
            if path in temp_map:
                result.append(str(temp_map[path]))
            else:
                result.append(arg)
        return result

    def _attach_listeners(self, ffmpeg: FFmpegAsync) -> None:
        """挂载 FFmpegAsync → MissionExecutor 的事件转发。"""

        def _on_started() -> None:
            self.emit(evt.STARTED)

        def _on_progress(current: object, total: object) -> None:
            self.emit(evt.PROGRESS_UPDATED, current, total)

        def _on_status(coding_info: object) -> None:
            self.emit(evt.STATUS_UPDATED, coding_info)

        def _on_finished() -> None:
            self.emit(evt.FINISHED)

        def _on_canceled() -> None:
            self.emit(evt.CANCELED)

        def _on_terminated() -> None:
            # FFmpegAsync 的 terminated 映射为 MissionExecutor 的 failed
            self.emit(evt.FAILED, _("FFmpeg 执行失败"))

        def _on_verbose(line: str) -> None:
            self.emit(evt.VERBOSE, line)

        ffmpeg.on(evt.STARTED, _on_started)
        ffmpeg.on(evt.PROGRESS_UPDATED, _on_progress)
        ffmpeg.on(evt.STATUS_UPDATED, _on_status)
        ffmpeg.on(evt.FINISHED, _on_finished)
        ffmpeg.on(evt.CANCELED, _on_canceled)
        ffmpeg.on("terminated", _on_terminated)
        ffmpeg.on(evt.VERBOSE, _on_verbose)

    def _commit_outputs(self, temp_map: dict[Path, Path]) -> MissionResult:
        """原子重命名临时文件到目标路径。

        每个文件独立重命名，成功后从 garbage 移除。
        任一文件重命名失败则整体返回 FAILED，剩余临时文件保留为 garbage。
        """
        for target, temp in temp_map.items():
            try:
                os.replace(temp, target)
                self._garbage_files.discard(temp)
            except OSError as e:
                self.emit(
                    evt.FAILED,
                    _("重命名临时文件失败: {error}").format(error=e),
                )
                return MissionResult.FAILED
        return MissionResult.SUCCESS
