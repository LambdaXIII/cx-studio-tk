"""本地化 Markdown 教程渲染。"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

from rich.align import Align
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel

__all__ = ["render_tutorial"]


def _detect_locale() -> str:
    """检测 locale。

    顺序：LANGUAGE → LC_ALL → LC_MESSAGES → LANG → zh_CN。
    跳过空值以及 C / C.UTF-8；从 ``en_US.UTF-8`` 中提取 ``en_US``。
    """
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var, "")
        if value and value not in ("C", "C.UTF-8"):
            return value.split(".", 1)[0].replace("-", "_")
    return "zh_CN"


def render_tutorial(
    package: str,
    filename: str,
    title: str | None = None,
    *,
    locale: str | None = None,
    width: int = 90,
    style: str = "bright_black",
    align: bool = True,
) -> RenderableType:
    """加载并渲染本地化 Markdown 教程。

    消除各工具中重复的 ``show_full_help`` 代码。locale 检测不依赖 cx-studio。

    加载顺序：
    1. ``<stem>.<locale><ext>``（locale 非 zh_CN 且非 C 时）
    2. ``<filename>``（回退到源语言）

    Args:
        package: 包名，用于 importlib.resources 加载
        filename: 基础文件名，如 ``help.md``
        title: 面板标题
        locale: 显式指定 locale；None 时检测环境变量
        width: 面板宽度
        style: 面板样式
        align: 是否整体居中对齐

    Returns:
        Panel 包裹的 Markdown（可选 Align.center 包装）

    Raises:
        FileNotFoundError: 指定文件在包中不存在
        ImportError: 包无法导入
    """
    if locale is None:
        locale = _detect_locale()

    stem = Path(filename).stem
    ext = Path(filename).suffix

    candidates = [filename]
    if locale not in ("zh_CN", "C"):
        candidates.insert(0, f"{stem}.{locale}{ext}")

    text: str | None = None
    tried: list[str] = []
    for fname in candidates:
        try:
            text = resources.files(package).joinpath(fname).read_text(encoding="utf-8")
            break
        except FileNotFoundError:
            tried.append(fname)
            continue

    if text is None:
        raise FileNotFoundError(f"在包 {package!r} 中找不到教程文件：已尝试 {tried!r}")

    panel = Panel(
        Markdown(text),
        title=title,
        width=width,
        style=style,
        expand=False,
    )
    if align:
        return Align.center(panel, width=width)
    return panel
