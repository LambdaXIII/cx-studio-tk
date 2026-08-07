"""IAppContext — 应用上下文抽象基类。

定义所有 CLI 工具上下文（`<Tool>Context`）的统一契约：持有参数解析结果和运行时状态，
实现上下文管理器协议以管理临时资源（如临时目录）的生命周期。
"""

from abc import ABC
from pathlib import Path
from tempfile import TemporaryDirectory


class IAppContext(ABC):
    """应用上下文抽象基类。

    职责：
    - 持有命令行参数解析结果（工具特定字段由子类定义）
    - 提供运行时状态的统一容器（temp_dir 等惰性能力）
    - 实现上下文管理器协议（__enter__/__exit__ + start/stop）

    设计意图：
    - 将"参数数据"和"运行状态"统一到一个容器，避免散落在 Application 各处
    - Application 通过 IAppContext 接口依赖，不绑定具体实现
    - temp_dir 作为通用运行时能力，由 IAppContext 惰性提供
    - context 的生命周期由 Application 管理（在 __enter__ 中 start）

    生命周期：
        with IAppContext() as ctx:
            ...
    ── 进入时调用 start()（惰性初始化 temp_dir 等），退出时调用 stop()（清理）。

    子类约定：
    - 基类提供以下共享状态字段（默认 False，子类可通过 dataclass field 或 __init__ 覆盖）：
        debug_mode: bool
        pretending_mode: bool
    - 子类应定义以下字段（duck-typing 兼容，IAppEnvironment 通过 getattr 安全访问）：
        show_help: bool
        show_full_help: bool
    - 子类的 from_arguments() 工厂方法负责参数解析
    - 子类可覆盖 start()/stop() 增加工具特定的资源初始化/清理
    """

    def __init__(self) -> None:
        self._temp_dir: TemporaryDirectory | None = None
        # 共享状态字段——子类通过 dataclass field 或 __init__ 赋值覆盖
        if not hasattr(self, "debug_mode"):
            self.debug_mode: bool = False
        if not hasattr(self, "pretending_mode"):
            self.pretending_mode: bool = False

    def start(self) -> None:
        """启动上下文。惰性创建临时目录等通用资源。

        子类覆盖时应先调用 super().start()，再初始化工具特定资源。
        """
        if self._temp_dir is None:
            self._temp_dir = TemporaryDirectory()

    def stop(self) -> None:
        """停止上下文。清理临时目录等通用资源。

        子类覆盖时应先清理工具特定资源，再调用 super().stop()。
        幂等——多次调用无害。
        """
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

    def cleanup(self) -> None:
        """手动清理。等价于 stop()，支持非上下文管理器场景。"""
        self.stop()

    def __enter__(self) -> "IAppContext":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        self.stop()
        return False

    @property
    def temp_dir(self) -> Path:
        """临时目录路径。惰性创建——首次访问时创建 TemporaryDirectory。"""
        if self._temp_dir is None:
            self._temp_dir = TemporaryDirectory()
        return Path(self._temp_dir.name)
