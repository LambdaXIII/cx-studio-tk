"""Mission 执行诊断信息输出器。

将 MissionScheduler 的中继事件翻译为 appenv.whisper() 输出，
用于 --debug 模式下跟踪 executor 内部步骤的执行时序。

设计原则：
- 纯事件消费者：订阅 scheduler 的 mission_* 事件，不修改 scheduler/executor
- 仅 whisper 输出：所有输出走 appenv.whisper()，仅 --debug 模式可见
- 零业务耦合：不接触进度条、结果报告等业务输出
- 零状态：不暂存任何跨 handler 数据，所有信息从事件参数拉取

输出格式：
- whisper 行：`[M] [abc123] 消息内容`，其中 [M] 是任务标识（bright_black），
  abc123 是 ULID 前 6 位（dim green）
- detail 面板：标题含 `[M] [abc123] 面板标题`

事件订阅关系（全部从 scheduler 中继，参数统一为 index + ExecutorStatus）：
- mission_started → 任务启动通知
- mission_finished → 任务执行完成
- mission_canceling → 正在停止 FFmpeg（中断过程信号）
- mission_canceled → 任务已取消
- mission_failed → 失败原因（来自 status.failure_reason）
- mission_ffmpeg_started → FFmpeg 进程已启动（含命令行）
- mission_ffmpeg_failed → FFmpeg 异常诊断 WealthyDetailPanel
- mission_commit_renamed → 原子重命名成功
- mission_skipped → 跳过信息（目标已存在）
- scheduler_canceling → 调度器级取消全部
"""

from __future__ import annotations

from collections.abc import Callable

from cx_wealthy import WealthyDetailPanel

from cx_tools.app import IAppEnvironment
from cx_tools.i18n import _

from .scheduler import MissionScheduler, SCHEDULER_CANCELING
from ..media.executor import ExecutorStatus


class DebugReporter:
    """将 MissionScheduler 事件翻译为 whisper 诊断输出。

    订阅 scheduler 的 mission_* 中继事件，通过 appenv.whisper() 输出
    executor 内部步骤的时序信息。不修改 scheduler 或 executor，
    纯粹是事件消费者。

    Usage:
        reporter = DebugReporter(scheduler, appenv)
        reporter.attach()

    Args:
        scheduler: 要订阅的 MissionScheduler 实例
        env: 应用环境，提供 whisper() 输出通道
    """

    # TODO: 考虑直接添加 SAID 和 WHISPERED 事件，不再以路由方式输出信息

    def __init__(
        self,
        scheduler: MissionScheduler,
        env: IAppEnvironment,
    ) -> None:
        self._scheduler = scheduler
        self._env = env
        self._handlers: list[tuple[str, Callable]] = []

    def attach(self) -> None:
        """挂接所有事件 handler 到 scheduler。

        注册全部 mission_* 事件的 handler，用于 --debug 模式输出诊断信息。
        """
        self._subscribe("mission_started", self._on_mission_started)
        self._subscribe("mission_canceling", self._on_canceling)
        self._subscribe("mission_canceled", self._on_canceled)
        self._subscribe("mission_failed", self._on_failed)
        self._subscribe("mission_ffmpeg_started", self._on_ffmpeg_started)
        self._subscribe("mission_ffmpeg_failed", self._on_ffmpeg_failed)
        self._subscribe("mission_commit_renamed", self._on_commit_renamed)
        self._subscribe("mission_skipped", self._on_skipped)
        self._subscribe("mission_finished", self._on_mission_finished)
        # scheduler 级事件
        self._scheduler.on(SCHEDULER_CANCELING, self._on_scheduler_canceling)
        self._handlers.append((SCHEDULER_CANCELING, self._on_scheduler_canceling))

    def detach(self) -> None:
        """从 scheduler 移除所有已注册的 handler。

        对称于 attach()，清理所有事件订阅。
        """
        for event, handler in self._handlers:
            self._scheduler.remove_listener(event, handler)
        self._handlers.clear()

    def _subscribe(self, event: str, handler: Callable) -> None:
        """注册单个事件 handler 并记录到 _handlers。"""
        self._scheduler.on(event, handler)
        self._handlers.append((event, handler))

    # ── 辅助 ────────────────────────────────────────────────

    @staticmethod
    def _format_prefix(status: ExecutorStatus) -> str:
        """生成 whisper 行的任务标识前缀：[M] [abc123]"""
        short_id = status.mission_id[:6]
        return f"[bright_black]M[/] [dim green]{short_id}[/]"

    # ── 事件 handler ──────────────────────────────────────────

    def _on_mission_started(self, index: int, status: ExecutorStatus) -> None:
        """mission_started：输出任务启动通知。"""
        prefix = self._format_prefix(status)
        self._env.whisper(f"{prefix} [cx.success]{_('任务已启动')}[/]")

    def _on_mission_finished(self, index: int, status: ExecutorStatus) -> None:
        """mission_finished：任务执行完成。"""
        prefix = self._format_prefix(status)
        self._env.whisper(f"{prefix} [cx.success]{_('已完成')}[/]")

    def _on_ffmpeg_started(self, index: int, status: ExecutorStatus) -> None:
        """mission_ffmpeg_started：FFmpeg 进程启动，附带命令行。"""
        prefix = self._format_prefix(status)
        self._env.whisper(
            f"{prefix} [cx.success]{_('FFmpeg 已启动')}[/] "
            f"[cx.whisper]{_('命令')}：ffmpeg {' '.join(status.arguments)}[/]"
        )

    def _on_canceling(self, index: int, status: ExecutorStatus) -> None:
        """mission_canceling：中断已识别，正在停止 FFmpeg。"""
        prefix = self._format_prefix(status)
        reason = status.cancel_reason or ""
        self._env.whisper(f"{prefix} [cx.warning]{_('正在停止')} {reason}[/]")

    def _on_canceled(self, index: int, status: ExecutorStatus) -> None:
        """mission_canceled：任务已取消。"""
        prefix = self._format_prefix(status)
        self._env.whisper(f"{prefix} [cx.warning]{_('已取消')}[/]")

    def _on_failed(self, index: int, status: ExecutorStatus) -> None:
        """mission_failed：任务级失败。"""
        prefix = self._format_prefix(status)
        reason = status.failure_reason or ""
        self._env.whisper(f"{prefix} [cx.error]{_('失败')}: {reason}[/]")

    def _on_ffmpeg_failed(self, index: int, status: ExecutorStatus) -> None:
        """mission_ffmpeg_failed：FFmpeg 进程异常退出，渲染诊断面板。"""
        prefix = self._format_prefix(status)
        self._env.whisper(
            WealthyDetailPanel(
                {
                    _("退出状态码"): str(status.exit_code),
                    _("原始命令"): f"ffmpeg {' '.join(status.arguments)}",
                    _("异常信息"): status.error_tail,
                },
                title=f"{prefix} {_('FFmpeg 执行异常')}",
            )
        )

    def _on_skipped(self, index: int, status: ExecutorStatus) -> None:
        """mission_skipped：目标已存在，跳过执行。"""
        prefix = self._format_prefix(status)
        targets = ", ".join(status.skipped_targets) if status.skipped_targets else ""
        self._env.whisper(
            f"{prefix} [cx.whisper]{_('跳过')}（{_('目标已存在')}"
            f"{f': {targets}' if targets else ''}）[/]"
        )

    def _on_commit_renamed(self, index: int, status: ExecutorStatus) -> None:
        """mission_commit_renamed：原子重命名成功。"""
        prefix = self._format_prefix(status)
        target = status.commit_target or ""
        self._env.whisper(f"{prefix} [cx.whisper]{_('已提交')} {target}[/]")

    def _on_scheduler_canceling(self) -> None:
        """scheduler_canceling：调度器级取消全部。"""
        self._env.whisper(f"[cx.error]{_('正在取消全部任务')}[/]")
