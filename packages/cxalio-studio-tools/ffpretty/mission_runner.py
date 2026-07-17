"""MissionRunner — 单 Mission 生命周期管理。

自包含的单 Mission 执行单元，封装：
- 进度条创建/更新/销毁
- 临时文件追踪（FILE_LOGGED）
- 中断轮询
- Whisperer 挂接（转发 executor 内部 WHISPERED 事件到 IAppEnvironment.whisper()）
"""

from collections.abc import Callable

from rich.progress import Progress, TaskID

from cx_tools.app import IAppEnvironment
from media_killer.media import (
    FileLogType,
    Mission,
    MissionExecutor,
    MissionResult,
    Whisperer,
)
from media_killer.media.executor import (
    CANCELED,
    ExecutorStatus,
    FAILED,
    FfmpegErrorInfo,
    FILE_LOGGED,
    FINISHED,
    PROGRESS_UPDATED,
    SKIPPED,
    STARTED,
    STATUS_UPDATED,
)


class MissionRunner:
    """单 Mission 执行器。封装进度条、临时文件追踪、中断响应。"""

    def __init__(
        self,
        mission: Mission,
        progress: Progress,
        env: IAppEnvironment,
        pretending: bool = False,
    ):
        self._mission = mission
        self._progress = progress
        self._env = env
        self._pretending = pretending
        self._task_id: TaskID | None = None
        self._executor: MissionExecutor | None = None
        self._last_error_info: FfmpegErrorInfo | None = None
        self._last_status: ExecutorStatus | None = None
        self._file_handler: Callable[[FileLogType, list], None] | None = None

    @property
    def status(self):
        """执行器的当前状态快照，执行完成后可读取 error_tail 等字段。"""
        return (
            self._executor.status if self._executor is not None else self._last_status
        )

    def make_error_info(self) -> FfmpegErrorInfo | None:
        """返回当前或最近一次执行的 FFmpeg 错误信息对象。

        executor 运行时取自 live status，executor 已清时取自缓存的 _last_error_info。
        仅失败后调用有意义，但方法本身在任何时刻均可调用。
        """
        if self._executor is not None:
            return self._executor.make_error_info()
        return self._last_error_info

    def set_file_handler(self, handler: Callable[[FileLogType, list], None]):
        """注册 FILE_LOGGED 文件事件的外部处理器（用于 garbage 追踪）。"""
        self._file_handler = handler

    def cancel(self):
        """取消当前执行。幂等——executor 为 None 时无操作。"""
        if self._executor is not None:
            self._executor.cancel()

    def _wire(self, executor: MissionExecutor, summary: str):
        """挂载进度条 + 事件转发。"""
        self._task_id = self._progress.add_task(
            description=f"{summary}[cx.success]准备中...[/]", total=None
        )

        executor.on(
            STARTED,
            lambda: self._progress.update(
                self._task_id,  # type: ignore[arg-type]
                description=f"{summary}[cx.success]开始转码...[/]",
            ),
        )
        executor.on(
            PROGRESS_UPDATED,
            lambda cur, tot: self._progress.update(
                self._task_id,  # type: ignore[arg-type]
                completed=cur.total_seconds if hasattr(cur, "total_seconds") else None,
                total=(
                    tot.total_seconds if tot and hasattr(tot, "total_seconds") else None
                ),
            ),
        )
        executor.on(
            STATUS_UPDATED,
            lambda ci: self._progress.update(
                self._task_id,  # type: ignore[arg-type]
                description=f"{summary}[cx.debug][{ci.current_speed:.2f}x][/][cx.success]转码中[/]",
            ),
        )
        executor.on(
            FINISHED,
            lambda: self._progress.update(
                self._task_id,  # type: ignore[arg-type]
                description=f"{summary}[cx.success]转码完成[/]",
            ),
        )
        executor.on(
            FAILED,
            lambda: self._progress.update(
                self._task_id,  # type: ignore[arg-type]
                description=f"{summary}[cx.error]转码失败[/]",
            ),
        )
        executor.on(
            CANCELED,
            lambda: self._progress.update(
                self._task_id,  # type: ignore[arg-type]
                description=f"{summary}[cx.warning]已取消[/]",
            ),
        )

        if self._file_handler:
            executor.on(FILE_LOGGED, self._file_handler)

        Whisperer.attach(executor, self._env)
        self._executor = executor

    def _unwire(self):
        """清理进度条和内部状态。"""
        if self._task_id is not None:
            self._progress.remove_task(self._task_id)
        if self._executor is not None:
            self._last_status = self._executor.status
            self._last_error_info = self._executor.make_error_info()
        self._executor = None

    async def run(self) -> MissionResult:
        """执行 Mission。

        Returns:
            MissionResult: 执行结果
        """
        if self._pretending:
            from media_killer.media import MissionPretender

            executor = MissionPretender(self._mission)
        else:
            executor = MissionExecutor(self._mission)
        summary = (
            f"[cx.info][{len(self._mission.inputs)}->{len(self._mission.outputs)}][/]"
        )
        self._wire(executor, summary)
        try:
            return await executor.execute()
        finally:
            self._unwire()
