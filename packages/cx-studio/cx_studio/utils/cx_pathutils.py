import os
from pathlib import Path
import re


def normalize_path(
    path: Path | str, anchor: Path | str | None = None, follow_symlinks: bool = True
) -> Path:
    path = Path(path)
    anchor = Path(anchor) if anchor else Path.cwd()
    if not path.is_absolute():
        path = anchor.joinpath(path)
    return path.resolve() if follow_symlinks else path.absolute()


def normalize_suffix(suffix: str, with_dot=True) -> str:
    s = str(suffix).strip().strip(".").lower()
    return "." + s if with_dot else s


def force_suffix(source: Path | str, suffix: str) -> Path:
    if not source:
        return Path()
    source = Path(source)
    suffix = normalize_suffix(suffix)
    return Path(source if source.suffix == suffix else source.with_suffix(suffix))


def take_dir(source: Path) -> Path:
    source = normalize_path(source)
    return source if source.is_dir() else source.parent


def is_executable(cmd: Path) -> bool:
    cmd = normalize_path(cmd)
    return cmd.exists() and os.access(cmd, os.X_OK)


def is_file_in_dir(file: Path, dir: Path) -> bool:
    f = str(normalize_path(file).resolve().absolute())
    d = str(normalize_path(dir).resolve().absolute())
    # TODO: 考虑使用pathlib的relative_to方法，避免使用字符串比较
    return f in d


def get_basename(source: Path | str) -> str:
    return Path(source).stem


def get_parents(source: Path | str, level: int = 1, resolve_path: bool = True):
    if level < 1:
        return []
    path = Path(source).resolve() if resolve_path else Path(source)
    parts = path.parts
    begin_index = max(0, len(parts) - level)
    end_index = len(parts) - 1
    return parts[begin_index:end_index]


def get_posix_path(path: Path | str) -> str:
    path = str(path)
    path = re.sub(r"\\{2,}", r"\\", path)
    path = re.sub(r"/{2,}", r"/", path)
    path = re.sub(r"\\", r"/", path)
    return path
