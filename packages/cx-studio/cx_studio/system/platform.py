"""platform —— 系统平台类型标识与当前平台检测。

定义 SystemType 枚举（Windows / macOS / Linux / WSL / iOS / Android /
FreeBSD / 未知），并据此导出当前平台的检测结果：platform_code
（sys.platform 的原始值）与 current_os（SystemType 判定值）。
跨平台分派（如 CrossRunner）依赖 current_os 选择平台实现。
"""

import sys
from enum import StrEnum


def _is_wsl() -> bool:
    """检测是否运行于 WSL。

    sys.platform 在 WSL 下仍返回 "linux"，无法区分；WSL 内核的
    release 字符串始终包含 "microsoft"（WSL2 形如
    "5.15.90.1-microsoft-standard-WSL2"），原生 Linux 不含。
    """
    try:
        import platform as _platform

        return "microsoft" in _platform.release().lower()
    except Exception:
        return False


class SystemType(StrEnum):
    """系统平台类型枚举（StrEnum）。

    枚举值（value）为稳定的平台短标识（如 "win" / "linux"），可直接作
    字符串比较或映射键（如 CrossRunner.function_map）。成员语义与判定
    来源：

    - WINDOWS（"win"）：Windows 系。sys.platform 的 "win32" 或品牌名
      小写后以 "win" 开头
    - MACOS（"macos"）：sys.platform 的 "darwin"，或品牌名小写后以
      "macos" 开头（如 platform.platform() 的 "macOS-14.5-…"）
    - LINUX（"linux"）/ WSL（"wsl"）：以 "linux" 开头的平台代码；WSL
      与原生 Linux 依赖内核 release 是否含 "microsoft" 区分（见
      _is_wsl）
    - IOS / ANDROID / FREEBSD：对应平台前缀
    - UNKNOWN：无法识别任何已知平台时的兜底值

    平台标识 → 成员的完整映射规则见 from_platform()；模块级变量
    current_os 为本次运行环境的判定结果。
    """

    UNKNOWN = "unknown"
    WINDOWS = "win"
    LINUX = "linux"
    MACOS = "macos"
    WSL = "wsl"
    IOS = "ios"
    ANDROID = "android"
    FREEBSD = "freebsd"

    @classmethod
    def from_platform(cls, platform_code: str) -> "SystemType":
        """按平台标识字符串判定对应的 SystemType。

        兼容 sys.platform 值域（win32 / linux / darwin / freebsd / ios）
        与平台品牌名（如 platform.platform() 的 "macOS-14.5-…"）：输入
        lower() 后按前缀匹配；Linux 前缀还需区分 WSL 与原生 Linux，
        依赖内核 release 字符串，见 _is_wsl()。

        Args:
            platform_code: 平台标识字符串，如 "win32"、"linux"、
                "darwin"。

        Returns:
            匹配到的 SystemType；无法识别时返回 SystemType.UNKNOWN。
        """
        code = platform_code.lower()
        if code.startswith("darwin") or code.startswith(cls.MACOS):
            return cls.MACOS
        if code.startswith(cls.WINDOWS):
            return cls.WINDOWS
        if code.startswith(cls.LINUX):
            return cls.WSL if _is_wsl() else cls.LINUX
        if code.startswith(cls.IOS):
            return cls.IOS
        if code.startswith(cls.ANDROID):
            return cls.ANDROID
        if code.startswith(cls.FREEBSD):
            return cls.FREEBSD
        return cls.UNKNOWN


platform_code = sys.platform
current_os: SystemType = SystemType.from_platform(platform_code)
