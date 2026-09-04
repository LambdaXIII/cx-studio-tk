"""opener —— 跨平台「用系统默认程序打开」操作。

基于 CrossRunner 构建 system_open 实例并注册平台实现：Windows 用
os.startfile，macOS 用 open，Linux 用 xdg-open（Popen 启动，不阻塞
等待）。调用 system_open(path)：路径存在且成功启动返回 True，否则
返回 False；未注册实现平台的调用抛 NotImplementedError。
"""

from pathlib import Path

from .cross_runner import CrossRunner
from .platform import SystemType

__all__ = ["system_open"]

system_open = CrossRunner()


@system_open.for_system(SystemType.WINDOWS)
def __open_windows(path: Path) -> bool:
    """Windows 打开文件"""
    import os

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
    """macOS 打开文件"""
    import subprocess

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
    """Linux 打开文件"""
    import subprocess

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
