"""cross_runner —— 跨平台执行注册表（按系统分派）。

CrossRunner 为每种平台（SystemType）注册独立的实现函数，实例被调用时
按当前平台自动选择实现并转发参数，屏蔽平台差异。典型应用：opener 的
system_open（Windows startfile / macOS open / Linux xdg-open）。
"""

from typing import Any, Callable

from . import platform


class CrossRunner:
    """按系统类型注册并分派执行函数的注册表（Registry 模式）。

    为各 SystemType 注册平台实现（register_function() / for_system()
    装饰器），实例调用（__call__）时按当前平台 platform.current_os
    取出对应函数并转发全部参数；该平台未注册任何实现时抛
    NotImplementedError。

    Attributes:
        function_map: 平台实现注册表，SystemType → 实现函数。
    """

    def __init__(self):
        self.function_map: dict[platform.SystemType, Callable[..., Any]] = {}

    def register_function(
        self, system_type: platform.SystemType, f: Callable[..., Any]
    ):
        """为指定平台类型注册实现函数。

        Args:
            system_type: 目标平台类型。
            f: 平台实现函数，实例调用时转发 __call__ 收到的全部参数。
                同一平台重复注册会覆盖旧实现。
        """
        self.function_map[system_type] = f

    def unregister_function(self, system_type: platform.SystemType):
        """移除指定平台类型的实现函数。

        Args:
            system_type: 目标平台类型。

        Raises:
            KeyError: 该平台类型尚未注册任何函数。
        """
        del self.function_map[system_type]

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        f = self.function_map.get(platform.current_os)
        if f is None:
            raise NotImplementedError(
                f"Platform {platform.current_os} not implemented."
            )
        return f(*args, **kwds)

    def for_system(self, system_type: platform.SystemType):
        """生成把函数注册到指定平台的装饰器。

        典型用法：:

            @runner.for_system(SystemType.WINDOWS)
            def impl(path): ...

        Args:
            system_type: 目标平台类型。

        Returns:
            装饰器：调用 register_function() 注册后原样返回被装饰函数。
        """

        def decorator(f: Callable[..., Any]):
            self.register_function(system_type, f)
            return f

        return decorator
