"""跨平台的路径处理工具函数集。

提供路径规范化、文件后缀处理、目录归属判断、可执行判断与命令行
引号转义等纯函数工具。多数函数同时接受 str 与 Path，输出为 Path
或字符串，无内部状态、可安全并发调用。
"""

import os
import re
from pathlib import Path, PurePath

from typing import Literal
from collections.abc import Iterable


def normalize_path(
    path: Path | str, anchor: Path | str | None = None, follow_symlinks: bool = True
) -> Path:
    """将路径规范化为绝对路径。

    相对路径以 anchor 为基准拼接（anchor 缺省为当前工作目录）。
    follow_symlinks=True 时调用 resolve()（解析符号链接，在
    Windows 上同时规范化大小写与分隔符）；否则仅调用 absolute()
    转为绝对路径。

    Args:
        path: 待规范化的路径。
        anchor: 相对路径的基准目录；None 时使用当前工作目录。
        follow_symlinks: True 时解析符号链接并规范化；False 时
            仅转为绝对路径，不做链接解析。

    Returns:
        规范化后的绝对 Path。
    """
    path = Path(path)
    anchor = Path(anchor) if anchor else Path.cwd()
    if not path.is_absolute():
        path = anchor.joinpath(path)
    return path.resolve() if follow_symlinks else path.absolute()


def normalize_suffix(suffix: str, with_dot: bool = True) -> str:
    """规范化文件后缀字符串。

    去除首尾空白与所有前导点并转为小写；with_dot=True 时确保结果
    带单个前导点。空后缀（或全为空白/点）返回空字符串。

    Args:
        suffix: 原始后缀，如 "TXT"、".txt"、" txt "。
        with_dot: True 时返回带前导点的形式（如 ".txt"）；
            False 时返回不带点的形式（如 "txt"）。

    Returns:
        规范化后的后缀字符串。
    """
    if not suffix:
        return ""
    s = str(suffix).strip().strip(".").lower()
    return "." + s if with_dot else s


def force_suffix(source: Path | str, suffix: str) -> Path:
    """强制路径使用指定后缀，不一致时整体替换。

    后缀经 normalize_suffix 规范化后与路径当前后缀比较：一致则原样
    返回；不一致则用 with_suffix 替换（覆盖原有后缀，而非追加）。
    空 source 返回空 Path()。

    Args:
        source: 源文件路径；为空时返回 Path()。
        suffix: 目标后缀，如 ".txt"。

    Returns:
        后缀与 suffix 一致的 Path。
    """
    if not source:
        return Path()
    source = Path(source)
    suffix = normalize_suffix(suffix)
    return Path(source if source.suffix == suffix else source.with_suffix(suffix))


def auto_suffix(source: Path | str, suffix: str) -> PurePath:
    """仅在路径没有后缀时补上指定后缀。

    已有后缀的路径保持不变（不覆盖现有后缀）；无后缀的路径追加
    指定后缀。空 source 返回空 Path()。

    Args:
        source: 源文件路径；为空时返回 Path()。
        suffix: 待追加的后缀，如 ".txt"。

    Returns:
        原路径或追加后缀后的 PurePath。
    """
    if not source:
        return Path()
    source = Path(source)
    if source.suffix:
        return source
    return source.with_suffix(suffix)


def take_dir(source: Path) -> Path:
    """返回路径的“目录形态”：目录返回自身，否则返回其父目录。

    常用于将“文件”参数安全地当作目录使用（如取某文件所在目录）。
    目录判定依赖文件系统状态（is_dir()）。

    Args:
        source: 待处理的路径。

    Returns:
        目录本身或其父目录（均已规范化）。
    """
    source = normalize_path(source)
    return source if source.is_dir() else source.parent


def is_executable(cmd: Path) -> bool:
    """判断路径是否真实存在且当前用户可执行。

    Args:
        cmd: 候选可执行文件路径。

    Returns:
        True 当且仅当路径存在且通过 os.access(…, os.X_OK) 检查。
        注意：目录通常也具备执行权限，因此对目录可能返回 True，
        本函数不区分文件与目录类型。
    """
    cmd = normalize_path(cmd)
    return cmd.exists() and os.access(cmd, os.X_OK)


def is_file_in_dir(file: Path, dir: Path) -> bool:
    """判断 file 是否位于 dir 目录内（含子目录）。

    归一化大小写与分隔符后做前缀比较；rstrip(os.sep) 保证
    dir 为根目录（如 "C:\\"、"/"）时边界正确，避免
    "C:\\foo\\bar" 与 "C:\\foo\\bar2" 类误判。

    Args:
        file: 待判断的文件路径。
        dir: 候选父目录路径。

    Returns:
        file 位于 dir 内（含任意层级子目录）时为 True，否则为 False。
    """
    f = os.path.normcase(str(normalize_path(file).resolve()))
    d = os.path.normcase(str(normalize_path(dir).resolve()))
    return f.startswith(d.rstrip(os.sep) + os.sep)


def get_basename(source: Path | str) -> str:
    """返回不含后缀的文件主名。

    Args:
        source: 文件路径。

    Returns:
        路径的 stem（去掉最后一个后缀后的文件名），
        如 "a/b.tar.gz" -> "b.tar"。
    """
    return Path(source).stem


def get_parents(
    source: Path | str, level: int = 1, resolve_path: bool = True
) -> Iterable[str]:
    """返回各级父目录部件（不包含文件自身）。

    按路径部件自文件名的上一级向上截取 level 层；不足 level 层时
    从路径起点截取。level 小于 1 时返回空序列。

    Args:
        source: 源路径。
        level: 需要返回的父目录层级数。
        resolve_path: True 时先 resolve() 再取父级；False 时按
            字面路径处理。

    Returns:
        父目录部件字符串序列（根到叶顺序），例如 POSIX 路径
        "/a/b/c.txt" 且 level=2 时返回 ("a", "b")。
    """
    if level < 1:
        return []
    path = Path(source).resolve() if resolve_path else Path(source)
    parts = path.parts
    begin_index = max(0, len(parts) - 1 - level)
    end_index = len(parts) - 1
    return parts[begin_index:end_index]


def get_posix_path(path: Path | str) -> str:
    """将路径转为 POSIX 风格的字符串。

    先将连续的反斜杠/正斜杠折叠为单个，再把所有反斜杠替换为
    正斜杠（如 "C:\\a\\b" -> "C:/a/b"）。仅做分隔符规范化，
    保留大小写与盘符/前导斜杠等原有结构。

    Args:
        path: 待转换的路径。

    Returns:
        使用正斜杠分隔的路径字符串。
    """
    path = str(path)
    path = re.sub(r"\\{2,}", r"\\", path)
    path = re.sub(r"/{2,}", r"/", path)
    path = re.sub(r"\\", r"/", path)
    return path


PathQuoteMode = Literal["auto", "force", "escape", "none"]


def quote_path(path: str | Path | None, quote_mode: PathQuoteMode = "auto") -> str:
    """将路径转换为适合命令行/配置传递的字符串，处理空白与引号。

    path 为 None 时返回空字符串。quote_mode 决定处理方式：
        - "auto"（默认）：仅当路径包含空格时用双引号包裹；
        - "force"：无条件用双引号包裹；
        - "escape"：将每个空白字符替换为反斜杠加空格（如 "\\ "）；
        - "none"：不做任何处理，原样返回字符串化结果。

    Args:
        path: 待处理的路径；None 时返回空字符串。
        quote_mode: 引号/转义模式，见 PathQuoteMode。

    Returns:
        处理后的路径字符串。
    """
    if path is None:
        return ""

    path = str(path)
    if quote_mode == "force":
        return f'"{path}"'
    if quote_mode == "auto":
        return f'"{path}"' if " " in path else path
    if quote_mode == "escape":
        return re.sub(r"\s", "\\ ", path)

    return path


def ensure_parents(path: Path | str, touch_child: bool = False) -> Path:
    """确保路径的父目录存在，必要时创建空的子文件。

    先转为绝对路径，再递归创建父目录（mkdir parents=True,
    exist_ok=True，已存在时静默通过）；若 touch_child=True 且
    目标路径尚不存在，则创建该空文件。

    Args:
        path: 目标文件或目录路径。
        touch_child: True 时在目标路径不存在的情况下创建空文件。

    Returns:
        绝对化后的 Path（父目录已确保存在）。
    """
    path = Path(path).absolute()
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    if touch_child and not path.exists():
        path.touch()
    return path


def ensure_new_file(path: Path | str) -> Path:
    """返回一个当前不存在的文件路径，必要时在主名后追加下划线。

    若 path 已存在，则在主名（stem）后逐次追加一个 "_" 并保留目录与
    后缀重新组合，直到得到不存在的路径为止（例如已存在 "a.txt" 时
    依次尝试 "a_.txt"、"a__.txt"……）。本函数只探测与返回路径，
    不会创建任何文件。

    Args:
        path: 期望的文件路径。

    Returns:
        当前不存在的 Path；若传入路径本就不存在则原样返回。
    """
    path = Path(path)
    basename = path.stem
    suffix = ""
    while path.exists():
        suffix += "_"
        new_basename = basename + suffix
        path = path.with_stem(new_basename)
    return path
