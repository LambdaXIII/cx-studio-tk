"""跨平台文本文件编辑器启动器。

提供 ``TextFileOpener`` 类及便利函数 ``try_open_text_file()``，
用于在 CLI 工具中探测 ``EDITOR``/``VISUAL`` 环境变量并启动编辑器打开文件。

基于 ``cx_studio.system.CrossRunner`` 实现 OS 回退编辑器策略。
"""

# TODO: 将来完全重构

from __future__ import annotations

import asyncio
import os
import shlex
import shutil
import subprocess
from pathlib import Path

from cx_studio.system import CrossRunner, SystemType

# ── OS 回退编辑器策略 ────────────────────────────────────
# 当 EDITOR/VISUAL 均未设置时，按当前 OS 依次尝试候选编辑器。
# 通过 CrossRunner 注册，确保平台相关的回退列表隔离。

_fallback_probe = CrossRunner()


@_fallback_probe.for_system(SystemType.WINDOWS)
def _windows_fallbacks() -> list[str]:
    return ["code --wait", "notepad++.exe", "notepad"]


@_fallback_probe.for_system(SystemType.MACOS)
def _macos_fallbacks() -> list[str]:
    return ["open -t", "code --wait", "vim"]


@_fallback_probe.for_system(SystemType.LINUX)
def _linux_fallbacks() -> list[str]:
    return ["editor", "nano", "vim", "vi"]


@_fallback_probe.for_system(SystemType.WSL)
def _wsl_fallbacks() -> list[str]:
    return ["editor", "nano", "vim", "vi"]


# ── 探查与执行 ────────────────────────────────────────────


def _is_executable(name: str) -> bool:
    """检查命令名或路径是否可执行。"""
    if "/" in name or "\\" in name:
        return Path(name).is_file()
    return shutil.which(name) is not None


class TextFileOpener:
    """跨平台文本文件编辑器启动器。

    探测顺序（优先）：构造参数 > ``EDITOR`` 环境变量 > ``VISUAL``
    环境变量 > OS 回退策略。编辑器命令首次探测后缓存，避免重复
    查找。

    Args:
        editor: 手动指定编辑器命令（可选）。格式与 ``EDITOR``
            环境变量一致，如 ``"code --wait"``、``"vim"``。
    """

    def __init__(self, editor: str | None = None) -> None:
        self._editor_override = editor
        self._cached_editor: str | None = None

    @property
    def editor(self) -> str | None:
        """获取编辑器命令字符串，缓存首次探测结果。

        优先返回 ``__init__`` 传入的编辑器，其次 ``EDITOR``
        环境变量，再次 ``VISUAL`` 环境变量，最后 OS 回退策略。
        若均不可用返回 ``None``。
        """
        if self._editor_override is not None:
            return self._editor_override
        if self._cached_editor is not None:
            return self._cached_editor
        self._cached_editor = self._probe()
        return self._cached_editor

    def override_editor(self, editor: str) -> None:
        """手动覆盖编辑器路径，同时清除缓存。"""
        self._editor_override = editor
        self._cached_editor = None

    def open(self, path: str | Path, wait: bool = True) -> bool:
        """用编辑器打开指定文件。

        若编辑器启动失败（命令不存在、非零退出），返回 ``False``。
        文件不存在也返回 ``False``。

        Args:
            path: 要打开的文件路径。
            wait: 是否阻塞等待编辑器进程退出。默认 ``True``，
                表现为 ``git commit`` 式的"打开编辑器→用户编辑→
                关闭编辑器→继续"语义。``False`` 时后台启动编辑器
                立即返回。

        Returns:
            ``True`` 表示编辑器成功启动。
        """
        p = Path(path)
        if not p.exists():
            return False

        cmd = self.editor
        if not cmd:
            return False

        args = [*shlex.split(cmd), str(p)]
        try:
            if wait:
                subprocess.run(args, check=True)
            else:
                subprocess.Popen(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

    def _probe(self) -> str | None:
        # 1. 环境变量
        env = os.environ.get("EDITOR") or os.environ.get("VISUAL")
        if env is not None and _is_executable(shlex.split(env)[0]):
            return env

        # 2. OS 回退策略
        try:
            for cmd in _fallback_probe():
                if _is_executable(shlex.split(cmd)[0]):
                    return cmd
        except NotImplementedError:
            pass

        return None


# ── 便利函数 ──────────────────────────────────────────────


def try_open_text_file(
    path: str | Path,
    editor: str | None = None,
    wait: bool = True,
) -> bool:
    """便利函数：实例化 ``TextFileOpener`` 并打开文件。

    Args:
        path: 要打开的文件路径。
        editor: 可选，覆盖编辑器命令。
        wait: 是否阻塞等待编辑器退出。默认 ``True``。

    Returns:
        ``True`` 表示编辑器成功启动。
    """
    return TextFileOpener(editor=editor).open(path, wait)
