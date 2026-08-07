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
        """按平台标识映射 SystemType。

        兼容 sys.platform 值域（win32/linux/darwin/freebsd/ios）与品牌名
        （如 platform.platform() 返回的 "macOS-14.5-…"），lower() 后匹配。
        WSL 与原生 Linux 的区分依赖内核 release，见 _is_wsl()。
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
