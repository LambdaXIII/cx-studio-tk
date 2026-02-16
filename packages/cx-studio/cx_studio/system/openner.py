from pathlib import Path

from .corss_runner import CrossRunner
from .platform import SystemType

__all__ = ["system_open"]

system_open = CrossRunner()


@system_open.for_system(SystemType.WINDOWS)
def __open_windows(path: Path) -> bool:
    import os

    """Windows 打开文件"""
    if not path.exists():
        return False
    try:
        os.startfile(
            str(path.absolute().resolve())
        )  # 仅Windows支持，自动处理文件/文件夹
        return True
    except Exception:
        return False


@system_open.for_system(SystemType.MACOS)
def __open_macos(path: Path) -> bool:
    import subprocess

    """macOS 打开文件"""
    if not path.exists():
        return False
    try:
        subprocess.Popen(
            ["open", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        return False


@system_open.for_system(SystemType.LINUX)
def __open_linux(path: Path) -> bool:
    import subprocess

    """Linux 打开文件"""
    if not path.exists():
        return False
    try:
        subprocess.Popen(
            ["xdg-open", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        return False
