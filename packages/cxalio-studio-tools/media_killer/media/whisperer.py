"""Executor debug 消息转发器。

将 executor 内部发射的 WHISPERED 事件（debug 消息）转发到
IAppEnvironment.whisper()，即仅在 ``-v/--debug`` 模式下显示。

职责单一：纯事件转发，不负责格式化或状态管理。
"""

from typing import TYPE_CHECKING

from cx_tools.app import IAppEnvironment

from .executor import WHISPERED

if TYPE_CHECKING:
    from .executor import MissionExecutor


class Whisperer:
    """可调用对象，将 WHISPERED 事件转发为 ``env.whisper()``。

    每个 executor 实例化一个 Whisperer 并绑定到其 WHISPERED 事件上。
    消息前缀包含简短 mission ID，便于在 debug 输出中区分并发任务。

    Attributes:
        _prefix: Rich markup 格式的消息前缀 ``[bright_black]M[/] [dim green]⟨short_id⟩[/]``
        _env: 应用环境引用，用于 whisper() 调用
    """

    def __init__(self, executor: "MissionExecutor", env: IAppEnvironment) -> None:
        """初始化转发器并生成消息前缀。

        Args:
            executor: 关联的 MissionExecutor 实例，从中提取 mission_id 前 6 字符
            env: 应用环境，调用其 whisper() 方法输出 debug 消息
        """
        short_id = executor.status.mission_id[:6]
        self._prefix = f"[bright_black]M[/] [dim green]{short_id}[/]"
        self._env = env

    def __call__(self, msg: str) -> None:
        """转发一条 debug 消息。

        Args:
            msg: executor 内部发射的 debug 文本
        """
        self._env.whisper(f"{self._prefix} {msg}")

    @classmethod
    def attach(cls, executor: "MissionExecutor", env: IAppEnvironment) -> None:
        """在 executor 上安装 WHISPERED 事件处理器。

        便捷方法：创建 Whisperer 实例并绑定到 executor 的 WHISPERED 事件。
        pyee 的 listener 生命周期跟随 executor——executor GC 时自动释放。

        Args:
            executor: 目标 MissionExecutor 实例
            env: 应用环境
        """
        whisperer = cls(executor, env)
        executor.on(WHISPERED, whisperer)
