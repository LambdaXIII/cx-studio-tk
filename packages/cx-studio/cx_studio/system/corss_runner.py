from typing import Any
from typing import Callable

from . import platform


class CrossRunner:
    def __init__(self):
        self.function_map: dict[platform.SystemType, Callable] = {}

    def register_function(self, system_type: platform.SystemType, f: Callable):
        self.function_map[system_type] = f

    def unregister_function(self, system_type: platform.SystemType):
        del self.function_map[system_type]

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        f = self.function_map.get(platform.current_os)
        if f is None:
            raise NotImplementedError(
                f"Platform {platform.current_os} not implemented."
            )
        return f(*args, **kwds)

    def for_system(self, system_type: platform.SystemType):
        def decorator(f: Callable):
            self.register_function(system_type, f)
            return f

        return decorator
