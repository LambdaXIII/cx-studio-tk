from enum import StrEnum
import sys
from typing import Self


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
    def from_platform(cls, platform_code: str) -> Self:
        if platform_code.startswith(cls.WINDOWS):
            return cls.WINDOWS
        elif platform_code.startswith(cls.LINUX):
            if "microsoft" in platform_code:
                return cls.WSL
            else:
                return cls.LINUX
        elif platform_code.startswith(cls.MACOS):
            return cls.MACOS
        elif platform_code.startswith(cls.IOS):
            return cls.IOS
        elif platform_code.startswith(cls.ANDROID):
            return cls.ANDROID
        elif platform_code.startswith(cls.FREEBSD):
            return cls.FREEBSD
        else:
            return cls.UNKNOWN


platform_code = sys.platform
current_os: SystemType = SystemType.from_platform(platform_code)
