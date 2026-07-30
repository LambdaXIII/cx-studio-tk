"""Executor 装配工厂。

根据 Mission 和 MissionHQ 配置装配出正确的执行器实例：
- 真实模式 → MissionExecutor（含 Whisperer 和 FILE_LOGGED 转发）
- Pretend 模式 → MissionPretender（含虚拟时长）

职责单一：装配。不负责调度、进度显示或中断响应。
"""

from typing import TYPE_CHECKING

from cx_studio.core.cx_time import CxTime

from .executor import FILE_LOGGED, MissionExecutor
from .mission import Mission
from .pretender import MissionPretender
from .whisperer import Whisperer

if TYPE_CHECKING:
    from .mission_hq import MissionHQ


class ExecutorFactory:
    """执行器装配工厂。

    通过 MissionHQ 引用访问环境配置（pretending 状态、IAppEnvironment 等），
    为每个 Mission 创建正确配置的执行器实例。

    Attributes:
        _hq: 反向引用 MissionHQ，用于访问环境配置和事件总线
    """

    def __init__(self, hq: "MissionHQ"):
        """初始化工厂。

        Args:
            hq: MissionHQ 实例引用，工厂通过它访问 pretending / env / 事件总线
        """
        self._hq = hq

    def __call__(self, mission: Mission) -> MissionExecutor | MissionPretender:
        """可调用入口：根据 hq 的 pretending 状态分流。

        Args:
            mission: 待执行的 Mission

        Returns:
            MissionExecutor: 真实模式
            MissionPretender: Pretend 模式
        """
        if self._hq._pretending:
            return self._build_pretender(mission)
        return self._build_executor(mission)

    def _build_pretender(self, mission: Mission) -> MissionPretender:
        """装配模拟执行器。

        查找源文件实际时长作为模拟转码的 duration；挂载 Whisperer 和
        FILE_LOGGED 转发器（对齐 _build_executor 的行为），确保
        --pretend 模式下同样能追踪 appenv.processed_files/generated_files。

        Args:
            mission: 待执行的 Mission

        Returns:
            MissionPretender: 已配置的模拟器
        """
        # 优先从 HQ 缓存读取（_duration_for 惰性填充），避免重复 MediaDB 查询
        cached_seconds = self._hq._mission_duration_cache.get(mission)
        if cached_seconds is not None and cached_seconds > 0:
            duration = CxTime.from_seconds(cached_seconds)
        else:
            duration = self._lookup_duration(mission)
        pretender = MissionPretender(mission, duration=duration)
        if self._hq._env:
            Whisperer.attach(pretender, self._hq._env)
        pretender.on(
            FILE_LOGGED,
            lambda t, paths: self._hq.emit(FILE_LOGGED, t, paths),
        )
        return pretender

    def _build_executor(self, mission: Mission) -> MissionExecutor:
        """装配真实执行器。

        挂载两个外部组件：
        1. Whisperer：将 debug 消息转发到 IAppEnvironment.whisper()
        2. FILE_LOGGED 转发器：将文件事件桥接到 MissionHQ 总线

        Args:
            mission: 待执行的 Mission

        Returns:
            MissionExecutor: 已装配的真实执行器
        """
        executor = MissionExecutor(mission)
        if self._hq._env:
            Whisperer.attach(executor, self._hq._env)
        executor.on(
            FILE_LOGGED,
            lambda t, paths: self._hq.emit(FILE_LOGGED, t, paths),
        )
        return executor

    def _lookup_duration(self, mission: Mission) -> CxTime | None:
        """从 media_db 查找源文件原始时长。

        Pretend 模式下用于模拟转码时长；Real 模式下供 MissionHQ._duration_for
        惰性填充进度条时长预估。media_db 不可用时返回 None。

        Args:
            mission: 待查找的 Mission

        Returns:
            CxTime: 源文件实际时长
            None: media_db 不可用或查找失败
        """
        media_db = self._hq._media_db
        if media_db is not None:
            info = media_db.get_media_info(mission.source)
            if info is not None and info.duration is not None:
                return CxTime.from_seconds(info.duration)
        return None
