"""条目模型——`Entry`、`EntryStatus` 与 JSON 序列化。

冻结值对象：状态转移用 `dataclasses.replace` 产生新实例，不原地修改。
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EntryStatus(Enum):
    """条目三态。

    `value` 是 JSON 里的英文 token（`todo`/`pending`/`done`），供脚本消费，
    不参与 i18n；人读显示（待办/进行中/已完成）由渲染层映射。
    """

    TODO = "todo"
    PENDING = "pending"
    DONE = "done"


@dataclass(frozen=True)
class Entry:
    """一条笔记：内容 + 三态 + 日期，归属一个域。

    Attributes:
        id: 4 位小写 base36 标识，全库唯一，生成后终身不变。
        domain: 所属域字面（首见字面，由 NoteStore 归一登记）。
        content: 条目内容，可含真实换行（多行按 Markdown 渲染）。
        status: 三态之一。
        created_at: 创建时间（本地朴素时间）。
        completed_at: 完成打点时间；仅 `DONE` 态持有，复位时清空。
    """

    id: str
    domain: str
    content: str
    status: EntryStatus
    created_at: datetime
    completed_at: datetime | None


def entry_to_json(e: Entry) -> dict:
    """把条目序列化为 JSON 兼容 dict。

    datetime 以 `isoformat(timespec="seconds")` 输出（本地朴素时间）；
    `completed_at` 为 None 时 JSON 里也是 `null`——键全量在场，消费方
    不需要探测。

    Args:
        e: 待序列化的条目。

    Returns:
        键为 `id/domain/content/status/created_at/completed_at` 的 dict。
    """
    return {
        "id": e.id,
        "domain": e.domain,
        "content": e.content,
        "status": e.status.value,
        "created_at": e.created_at.isoformat(timespec="seconds"),
        "completed_at": (
            e.completed_at.isoformat(timespec="seconds") if e.completed_at else None
        ),
    }


def entry_from_json(d: dict) -> Entry:
    """从 JSON dict 反序列化为条目。

    Args:
        d: `entry_to_json` 产出的 dict；容忍缺失 `completed_at` 键（视为 None）。

    Returns:
        等值的 `Entry` 实例。

    Raises:
        KeyError: 缺失必需键。
        ValueError: 时间戳或 status token 非法。
    """
    completed_raw = d.get("completed_at")
    return Entry(
        id=d["id"],
        domain=d["domain"],
        content=d["content"],
        status=EntryStatus(d["status"]),
        created_at=datetime.fromisoformat(d["created_at"]),
        completed_at=(
            datetime.fromisoformat(completed_raw) if completed_raw is not None else None
        ),
    )
