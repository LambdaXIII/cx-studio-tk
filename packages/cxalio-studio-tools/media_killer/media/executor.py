"""单 Mission 执行单元。

本模块是 media_killer 共享底座的一部分，包含单 Mission 执行所需的全部符号。
MissionExecutor 通过 asyncio 运行 FFmpeg，使用 pyee 事件模型向外报告进度和状态，
通过 cancel() 接收外部中断。不依赖 appenv。

内容：
- MissionExecutor：单 Mission 执行单元（AsyncIOEventEmitter 子类），
  校验→创建目录→运行 FFmpeg→原子提交，支持外部取消和临时文件保护。
- MissionResult：执行结果枚举（SUCCESS/FAILED/CANCELED）。
- 事件名常量：STARTED、PROGRESS_UPDATED、STATUS_UPDATED、FINISHED、
  FAILED、CANCELED、VERBOSE、SKIPPED。
"""

import asyncio
from dataclasses import dataclass
import os
from enum import Enum
from pathlib import Path

from pyee.asyncio import AsyncIOEventEmitter

from cx_studio.ffmpeg import (
    FFMPEG_EVENT_CANCELED,
    FFMPEG_EVENT_FINISHED,
    FFMPEG_EVENT_PROGRESS_UPDATED,
    FFMPEG_EVENT_STARTED,
    FFMPEG_EVENT_STATUS_UPDATED,
    FFMPEG_EVENT_TERMINATED,
    FFMPEG_EVENT_VERBOSE,
    FFmpegCodingInfo,
    FFmpegAsync,
)
from cx_studio.filesystem import CmdFinder
from cx_tools.i18n import _

from .mission import Mission

# ── 事件名常量 ──────────────────────────────────────────────

# FFmpeg 进程已启动
STARTED: str = "started"
# 进度更新：(current: CxTime, total: CxTime | None)
PROGRESS_UPDATED: str = "progress_updated"
# 帧级状态更新：(coding_info: FFmpegCodingInfo)
STATUS_UPDATED: str = "status_updated"
# 转码成功完成
FINISHED: str = "finished"
# 转码失败：()，无参信号。失败原因通过 status.failure_reason 拉取
FAILED: str = "failed"
# 被外部取消：()，无参信号。取消原因通过 status.cancel_reason 拉取。
# 与 CANCELING 的区别：CANCELING = 中断请求已识别/正在停止（过程），
# CANCELED = 已停止（终态）。
CANCELED: str = "canceled"
# FFmpeg 原始 stderr 行：(line: str)
VERBOSE: str = "verbose"
# 任务被跳过（目标已存在且 overwrite=False）：()，无参信号。
# 已存在的目标文件路径通过 status.skipped_targets 拉取。
SKIPPED: str = "skipped"
# 参数构建完成：()，无参信号。完整命令行参数通过 status.arguments 拉取。
# 在 _build_arguments() 返回后、FFmpegAsync 启动前发射。
ARGS_BUILT: str = "args_built"

# 单个输出文件原子重命名成功：()，无参信号。
# 重命名的目标文件名通过 status.commit_target 拉取。
# 在 os.replace(temp, target) 成功后、从 garbage_files 移除后发射。
# 每次 _commit_outputs() 遍历成功一个文件就发射一次。
# 注意：MissionPretender 不发射此事件（不创建临时文件）。
COMMIT_RENAMED: str = "commit_renamed"

# ── FFmpeg 进程级事件（executor 转发自 FFmpegAsync，与 executor 自身事件独立）──

# FFmpeg 进程已启动：()，无参信号。命令行通过 status.arguments 拉取。
# 由 _attach_listeners 从 FFmpegAsync 的 FFMPEG_EVENT_STARTED 转发。
# 与 executor 的 STARTED 不同——STARTED 表示 executor 开始执行
# （校验通过、参数构建完成），FFMPEG_STARTED 表示 FFmpeg 子进程
# 实际启动。Pretender 不发射此事件（不启动 FFmpeg）。
FFMPEG_STARTED: str = "ffmpeg_started"

# FFmpeg 进程正常退出（returncode == 0）：()
# 由 _attach_listeners 从 FFmpegAsync 的 FFMPEG_EVENT_FINISHED 转发。
# 与 executor 的 FINISHED 不同——FINSIHED 在 _commit_outputs
# 成功后由 executor 发射，表示任务完整完成（含原子提交）。
# FFMPEG_FINISHED 仅表示 FFmpeg 进程本身成功退出。
# Pretender 不发射此事件。
FFMPEG_FINISHED: str = "ffmpeg_finished"

# FFmpeg 进程异常退出（returncode != 0，非取消）：()，无参信号。
# 退出码/命令/错误尾巴通过 status.exit_code / status.arguments / status.error_tail 拉取。
# 由 _attach_listeners 从 FFmpegAsync 的 FFMPEG_EVENT_TERMINATED 转发，
# 提取错误尾巴后存入 status 再发射。与 executor 的 FAILED 独立——
# FAILED 表示任务级失败摘要，FFMPEG_FAILED 携带 FFmpeg 进程级的完整诊断上下文。
# 两者在 FFmpeg 异常退出时先后触发：先 FFMPEG_FAILED（进程级详情），
# 再 FAILED（任务级摘要）。Pretender 不发射此事件。
FFMPEG_FAILED: str = "ffmpeg_failed"

# executor 识别到中断信号，即将停止 FFmpeg 进程：()
# 在 ffmpeg.cancel() 调用前发射。无参信号，数据通过 status 属性拉取。
# 与 CANCELED 的区别：
# CANCELING = "我收到了中断请求，正在停止"（过程信号）
#   → status.cancel_reason 可区分取消来源
# CANCELED = "已停止，任务取消"（终态信号）
CANCELING: str = "canceling"


# ── MissionResult 枚举 ──────────────────────────────────────


class MissionResult(Enum):
    """Mission 执行结果。

    Attributes:
        SUCCESS: 转码成功完成
        FAILED: 转码失败（校验失败或 FFmpeg 异常退出）
        CANCELED: 被外部取消
        SKIPPED: 目标已存在且 overwrite=False，执行时跳过
    """

    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"
    SKIPPED = "skipped"


# ── ExecutorStatus 数据快照 ──────────────────────────────────


@dataclass
class ExecutorStatus:
    """executor 运行时动态信息的只读快照。

    通过 MissionExecutor.status 属性暴露，供事件接收端拉取。
    所有字段在事件发射前已就绪——接收端在 handler 中读取 status
    即可获得触发该事件时的完整上下文。

    事件分为两类：
    - **无参信号**（大部分生命周期事件）：emit() 不携带参数，
      接收端通过 executor.status 拉取数据。此类信号反映状态跃迁，
      如 STARTED、CANCELING、CANCELED、FAILED、FINISHED 等。
    - **流式数据事件**（PROGRESS_UPDATED、STATUS_UPDATED、VERBOSE）：
      保留 emit 参数，因为是高频流式数据，不适合快照模式。
    """

    mission_id: str  # 当前 mission 的 ULID 字符串
    mission_name: str  # 源文件名（不含扩展名）
    arguments: list[str]  # FFmpeg 完整命令行参数（已替换临时路径）
    exit_code: int | None  # FFmpeg 进程退出码（仅 FFMPEG_FAILED 后有效）
    error_tail: str  # FFmpeg 错误尾巴（仅 FFMPEG_FAILED 后有效）
    cancel_reason: str | None  # 取消原因（仅 CANCELING/CANCELED 后有效）
    failure_reason: str | None  # 任务级失败原因（校验失败、重命名失败等）
    skipped_targets: list[str]  # 被跳过的已存在目标文件路径列表
    commit_target: str | None  # 最近一次原子重命名的目标文件名
    coding_info: FFmpegCodingInfo | None = None  # FFmpeg 运行时状态快照


# ── 模块级校验函数 ──────────────────────────────────────────


def validate_mission(mission: Mission, ffmpeg_executable: str) -> None:
    """校验 Mission 的合法性。校验失败抛出异常。

    检查项：输入输出重叠、FFmpeg 可执行性、输入文件存在性、
    输出目录可写性（仅检查已存在的目录，不创建目录）。

    此函数是纯校验，不产生副作用——不创建目录、不修改文件。
    MissionExecutor._validate() 和 MissionPretender.execute() 共用此函数。

    Args:
        mission: 待校验的 Mission
        ffmpeg_executable: FFmpeg 可执行文件路径

    Raises:
        ValueError: 校验失败时
    """
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
    # FFmpeg 可执行性（通过 CmdFinder 解析 PATH）
    resolved = CmdFinder.which(ffmpeg_executable)
    if resolved is None:
        raise ValueError(
            _("FFmpeg 可执行文件无效: {path}").format(path=ffmpeg_executable)
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


# ── MissionExecutor ─────────────────────────────────────────
class MissionExecutor(AsyncIOEventEmitter):
    """单 Mission 执行单元。

    继承 ``AsyncIOEventEmitter``，通过事件向外报告进度与状态。
    使用临时文件机制保证输出原子性：FFmpeg 写入 ``mk2tmp.<target>`` 临时文件，
    成功后原子重命名为目标文件；失败或取消时临时文件保留为 garbage。

    中断语义（两段式）：
    - 单次 Ctrl+C：调度器调用 ``executor.cancel()``（设置 ``_cancel_event``），
      本单元在轮询中检测到后发射 ``CANCELING``，停止 FFmpeg，返回 ``CANCELED``。
    - 二次 Ctrl+C（3 秒内）：调度器通过 ``task.cancel()`` 取消所有 task，
      本单元 ``asyncio.CancelledError`` 中发射 ``CANCELING``，停止 FFmpeg，返回 ``CANCELED``。

    信号与数据分离：
    所有生命周期事件（除流式数据 PROGRESS_UPDATED/STATUS_UPDATED/VERBOSE）
    均为无参信号——emit() 不携带参数。接收端通过 ``executor.status`` 属性
    （返回 ``ExecutorStatus`` 只读快照）拉取事件上下文数据。

    SKIPPED 语义：
    - 执行前检查目标文件是否存在且 overwrite=False，若全部目标均已存在则跳过
      执行返回 SKIPPED。与 CANCELED 的区别：SKIPPED 表示从未开始执行
      （FFmpeg 未启动），CANCELED 表示已开始执行后因中断中止。

    事件列表（无参信号，数据通过 status 拉取，除非注明）：
    - ``started`` — executor 开始执行
    - ``progress_updated`` — (current, total) 流式进度
    - ``status_updated`` — (coding_info) 帧级状态
    - ``finished`` — 任务完整完成
    - ``failed`` — 任务级失败 → status.failure_reason
    - ``canceled`` — 任务已取消 → status.cancel_reason
    - ``canceling`` — 中断已识别/正在停止 → status.cancel_reason
    - ``verbose`` — (line) FFmpeg stderr 流式行
    - ``skipped`` — 目标已存在跳过 → status.skipped_targets
    - ``ffmpeg_started`` — FFmpeg 子进程已启动 → status.arguments
    - ``ffmpeg_finished`` — FFmpeg 进程正常退出
    - ``ffmpeg_failed`` — FFmpeg 异常退出 → status.exit_code/arguments/error_tail
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
        self._ffmpeg_arguments: list[str] = []
        self._exit_code: int | None = None
        self._error_tail: str = ""
        self._cancel_reason: str | None = None
        self._failure_reason: str | None = None
        self._skipped_targets: list[str] = []
        self._commit_target: str | None = None
        self._coding_info: FFmpegCodingInfo | None = (
            None  # FFmpeg 运行时状态快照，用于总体进度轮询拉取
        )

    @property
    def status(self) -> ExecutorStatus:
        """返回当前运行时状态的只读快照。

        供事件接收端在 handler 中拉取数据。所有字段在对应事件
        发射前已就绪，反映触发该事件时的完整上下文。
        """
        # TODO:这里非常不优雅，将来考虑设计更通用、更安全的机制
        return ExecutorStatus(
            mission_id=str(self._mission.mission_id),
            mission_name=self._mission.name,
            arguments=self._ffmpeg_arguments,
            exit_code=self._exit_code,
            error_tail=self._error_tail,
            cancel_reason=self._cancel_reason,
            failure_reason=self._failure_reason,
            skipped_targets=self._skipped_targets,
            commit_target=self._commit_target,
            coding_info=self._coding_info,
        )

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

        流程：校验 → 跳过检查 → 创建输出目录 → 计算临时文件
        → 运行 FFmpeg → 提交或保留 garbage。

        Returns:
            MissionResult: 执行结果（SUCCESS/FAILED/CANCELED/SKIPPED）
        """
        # 校验阶段抛异常即 FAILED
        try:
            self._validate()
        except Exception as e:
            self._failure_reason = str(e)
            self.emit(FAILED)
            return MissionResult.FAILED

        # 覆盖检查：target 已存在且 overwrite=False → 跳过
        if not self._mission.overwrite:
            existing = [
                s.filename for s in self._mission.outputs if s.filename.exists()
            ]
            if existing:
                self._skipped_targets = [str(e) for e in existing]
                self.emit(SKIPPED)
                return MissionResult.SKIPPED

        # 创建输出目录
        self._ensure_output_dirs()

        # 计算临时文件映射：目标路径 → 临时路径
        temp_map: dict[Path, Path] = {}
        for output_spec in self._mission.outputs:
            target = output_spec.filename
            temp = target.parent / f"{self._TEMP_PREFIX}{target.name}"
            temp_map[target] = temp

        # 启动前登记 garbage
        for temp in temp_map.values():
            self._garbage_files.add(temp)

        # 启动前清理已存在的临时文件（上次异常退出可能残留）
        for temp in temp_map.values():
            temp.unlink(missing_ok=True)

        # 构建参数：替换输出路径为临时路径
        arguments = self._build_arguments(temp_map)
        self._ffmpeg_arguments = arguments
        self.emit(ARGS_BUILT)
        self.emit(STARTED)

        # 创建 FFmpeg 实例并挂载事件转发
        ffmpeg = FFmpegAsync(self._ffmpeg_executable)
        self._attach_listeners(ffmpeg)

        main_task: asyncio.Task | None = None

        try:
            main_task = asyncio.create_task(ffmpeg.execute(arguments))

            # 轮询等待，期间检查取消信号和第一次中断
            while not main_task.done():
                if self._cancel_event.is_set():
                    self._cancel_reason = _("用户中断")
                    self.emit(CANCELING)
                    ffmpeg.cancel()
                    await main_task
                    return MissionResult.CANCELED
                await asyncio.sleep(0.1)

            ffmpeg_ok: bool = main_task.result()

        except asyncio.CancelledError:
            self._cancel_reason = _("调度器强制取消")
            self.emit(CANCELING)
            ffmpeg.cancel()
            # 等待 ffmpeg 子进程完成清理后再返回，保证文件句柄释放
            if main_task is not None and not main_task.done():
                try:
                    await main_task
                except (asyncio.CancelledError, Exception):
                    pass
            return MissionResult.CANCELED

        except Exception as e:
            self._failure_reason = str(e)
            self.emit(FAILED)
            return MissionResult.FAILED

        # 用户取消优先于 FFmpeg 结果
        if self._cancel_event.is_set():
            return MissionResult.CANCELED

        if ffmpeg_ok:
            return self._commit_outputs(temp_map)

        # FFmpeg 异常退出
        self._failure_reason = _("FFmpeg 执行失败")
        self.emit(FAILED)
        return MissionResult.FAILED

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        """执行前校验。校验失败抛出异常。

        不创建目录——目录创建由 _ensure_output_dirs() 负责。
        """
        validate_mission(self._mission, self._ffmpeg_executable)

    def _ensure_output_dirs(self) -> None:
        """创建不存在的输出目录。"""
        output_dirs = {f.filename.parent for f in self._mission.outputs}
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
        """挂载 FFmpegAsync → MissionExecutor 的事件转发。

        FFmpeg 进程级事件转发到 executor 的 FFMPEG_ 系列
        （FFMPEG_STARTED/FFMPEG_FINISHED/FFMPEG_FAILED），
        与 executor 自身的 STARTED/FINISHED/FAILED 独立。
        progress_updated/status_updated/verbose 保持原有转发
        （executor 有自己的同名常量）。
        """

        def _on_ffmpeg_started() -> None:
            self.emit(FFMPEG_STARTED)

        def _on_progress(current: object, total: object) -> None:
            # 保持 _coding_info 与 FFmpeg 最新进度同步
            # _on_status 建立引用后，此处逐行更新 current_time/total_time
            # type: ignore 因为 FFmpeg 事件承诺传递 CxTime，
            # 但类型签名选择 object 以避免循环导入
            if self._coding_info is not None:
                self._coding_info.current_time = current  # type: ignore[assignment]
                self._coding_info.total_time = total  # type: ignore[assignment]
            self.emit(PROGRESS_UPDATED, current, total)

        def _on_status(coding_info: object) -> None:
            # 首次建立 / 更新 _coding_info 引用（FFmpegCodingInfo 副本）
            self._coding_info = coding_info  # type: ignore[assignment]
            self.emit(STATUS_UPDATED, coding_info)

        def _on_ffmpeg_finished() -> None:
            self.emit(FFMPEG_FINISHED)

        def _on_canceled() -> None:
            self.emit(CANCELED)

        def _on_ffmpeg_terminated(exit_code: int, stderr_lines: list[str]) -> None:
            self._exit_code = exit_code
            self._error_tail = self._extract_error_tail(stderr_lines)
            self.emit(FFMPEG_FAILED)

        def _on_verbose(line: str) -> None:
            self.emit(VERBOSE, line)

        ffmpeg.on(FFMPEG_EVENT_STARTED, _on_ffmpeg_started)
        ffmpeg.on(FFMPEG_EVENT_PROGRESS_UPDATED, _on_progress)
        ffmpeg.on(FFMPEG_EVENT_STATUS_UPDATED, _on_status)
        ffmpeg.on(FFMPEG_EVENT_FINISHED, _on_ffmpeg_finished)
        ffmpeg.on(FFMPEG_EVENT_CANCELED, _on_canceled)
        ffmpeg.on(FFMPEG_EVENT_TERMINATED, _on_ffmpeg_terminated)
        ffmpeg.on(FFMPEG_EVENT_VERBOSE, _on_verbose)

    def _commit_outputs(self, temp_map: dict[Path, Path]) -> MissionResult:
        """原子重命名临时文件到目标路径。

        每个文件独立重命名，成功后从 garbage 移除。
        任一文件重命名失败则整体返回 FAILED，剩余临时文件保留为 garbage。
        """
        for target, temp in temp_map.items():
            try:
                os.replace(temp, target)
                self._garbage_files.discard(temp)
                self._commit_target = str(target.name)
                self.emit(COMMIT_RENAMED)
            except OSError as e:
                self._failure_reason = _("重命名临时文件失败: {error}").format(error=e)
                self.emit(FAILED)
                return MissionResult.FAILED
        self.emit(FINISHED)
        return MissionResult.SUCCESS

    @staticmethod
    def _extract_error_tail(stderr_lines: list[str]) -> str:
        """从 FFmpeg stderr 中提取错误尾巴。

        找到最后一个包含 ``frame=`` 和 ``fps=`` 的进度行，
        返回其之后的所有行（即 FFmpeg 报错段）。
        若未找到任何进度行，退回取最后 10 行。

        Args:
            stderr_lines: FFmpeg stderr 的完整行列表

        Returns:
            str: 错误尾巴文本。若无输出则返回占位文本。
        """
        if not stderr_lines:
            return "（无 stderr 输出）"

        # 倒查最后一个进度行
        last_progress_idx: int = -1
        for idx, line in enumerate(stderr_lines):
            if "frame=" in line and "fps=" in line:
                last_progress_idx = idx

        if last_progress_idx >= 0:
            tail_lines = stderr_lines[last_progress_idx + 1 :]
            if not tail_lines:
                return "（最后一条为进度行，无后序错误行）"
            return "\n".join(tail_lines)

        # 无进度行：退回取末 10 行
        return "\n".join(stderr_lines[-10:])
