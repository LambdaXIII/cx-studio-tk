"""域解析——纯函数集合，不依赖 appenv。

域语义：域是**字面命名空间**，不是文件系统路径——
- 域字面统一为以 `/` 开头、不以 `/` 结尾的归一形式（根域为 `/`）；
- 身份键大小写不敏感（`canonical`），首见字面保留（由 NoteStore 登记）；
- 段的边界是 `/`：`/生活琐事2` 与 `/生活琐事` 互不包含（`is_within` 按段判定）。

`derive_from_cwd` 把当前工作目录映射为域：HOME 之下取相对字面，HOME
即根域，HOME 之外取去盘符绝对字面。
"""

import os
import re
from collections.abc import Iterable
from pathlib import Path

ROOT_DOMAIN = "/"

# Windows 盘符前缀（如 "E:"），归一时去除
_DRIVE_RE = re.compile(r"^[A-Za-z]:")
# 连续斜杠折叠
_MULTI_SLASH_RE = re.compile(r"/{2,}")


def normalize_domain_literal(literal: str) -> str:
    """把路径样式的字面归一为域字面。

    规则：`\\` 转 `/`；去 Windows 盘符；连续 `/` 折叠；去首尾多余的 `/`
    后补唯一前导 `/`（根域为 `/` 本身）；**不改大小写**（身份键归
    `canonical` 处理，字面保留原样）。

    Args:
        literal: 任意路径样式字面，如 `E:\\x\\y`、`/a/b/`。

    Returns:
        归一后的域字面，如 `/x/y`、`/a/b`、`/`。
    """
    s = literal.replace("\\", "/")
    s = _DRIVE_RE.sub("", s)
    s = _MULTI_SLASH_RE.sub("/", s)
    core = s.strip("/")
    return f"/{core}" if core else ROOT_DOMAIN


def derive_from_cwd(cwd: Path) -> str:
    """从工作目录推导当前域。

    HOME 判定用 `Path.home()` 与 `cwd` 各自 `resolve()` 后比较；Windows
    下前缀比较大小写不敏感，跨平台统一手动比较而不依赖
    `is_relative_to` 的平台行为差异。

    Args:
        cwd: 当前工作目录。

    Returns:
        HOME 之下 → `"/" + 相对字面` 归一化；HOME 本身 → `/`；
        HOME 之外 → 去盘符绝对字面。
    """
    home = Path.home().resolve()
    resolved = cwd.resolve()
    if resolved == home:
        return ROOT_DOMAIN
    resolved_str = str(resolved)
    home_str = str(home)
    if resolved_str.lower().startswith(home_str.lower() + os.sep):
        rel = resolved_str[len(home_str) + 1 :]
        return normalize_domain_literal("/" + rel)
    return normalize_domain_literal(resolved_str)


def resolve_domain(cwd: Path, domain_param: str | None, global_flag: bool) -> str:
    """解析本次命令生效的当前域。

    优先级：`-g` 根域 > `-p` 指定的域字面 > 由 cwd 推导。
    `-p` 字面以 `/`、`\\` 开头或带盘符时视为根绝对字面（与
    `derive_from_cwd` 的 HOME 外映射同一族）；否则**相对当前域**
    （cwd 推导结果）拼接，而不是相对 cwd 再推导一次。

    Args:
        cwd: 当前工作目录。
        domain_param: `-p/--path` 给出的域字面，可为 None。
        global_flag: 是否指定 `-g/--global`。

    Returns:
        归一化后的当前域字面。
    """
    if global_flag:
        return ROOT_DOMAIN
    if domain_param:
        if (
            domain_param.startswith("/")
            or domain_param.startswith("\\")
            or _DRIVE_RE.match(domain_param)
        ):
            return normalize_domain_literal(domain_param)
        return join_domain(derive_from_cwd(cwd), domain_param)
    return derive_from_cwd(cwd)


def join_domain(base: str, rel: str) -> str:
    """把相对字面拼接到基准域之下。

    Args:
        base: 基准域字面（按域字面归一）。
        rel: 相对字面（可带首尾 `/` 或 `\\` 分隔）。

    Returns:
        拼接并归一化后的域字面。
    """
    rel_s = rel.replace("\\", "/").strip("/")
    if not rel_s:
        return normalize_domain_literal(base)
    return normalize_domain_literal(
        normalize_domain_literal(base).rstrip("/") + "/" + rel_s
    )


def canonical(domain: str) -> str:
    """返回域的身份键（大小写不敏感合并用）。"""
    return domain.lower()


def is_within(domain: str, ancestor: str) -> bool:
    """判定 domain 是否落在 ancestor 域（含其自身）之内。

    按段边界比较：`/生活琐事2` 不在 `/生活琐事` 之内。

    Args:
        domain: 待判定的域字面。
        ancestor: 作为边界的祖先域字面。

    Returns:
        ancestor 为根域时恒 True；否则按身份键的段前缀比较。
    """
    if ancestor == ROOT_DOMAIN:
        return True
    a = canonical(ancestor).rstrip("/")
    d = canonical(domain)
    return d == a or d.startswith(a + "/")


def subdomains_of(current: str, known: Iterable[str]) -> list[str]:
    """从已知域集合中筛出 current 的可见域（含 current 自身）。

    Args:
        current: 当前域字面。
        known: 已登记的域字面集合。

    Returns:
        满足 `is_within(d, current)` 的域字面列表（保持输入序，调用方
        再排序）。
    """
    return [d for d in known if is_within(d, current)]
