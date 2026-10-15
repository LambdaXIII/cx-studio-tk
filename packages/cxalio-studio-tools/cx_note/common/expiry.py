"""终态超龄谓词——`is_expiring`。

运行时派生判断：不写入条目、不落盘，判据只有一个、由本模块唯一持有。
恰好三个消费方共用它——人读标记（超龄条目的界面标注）、
`--json` 输出投影、运行收尾的清理——不得各自另写规则。
"""

from datetime import datetime, timedelta

from cx_note.common.domain import is_within
from cx_note.common.entry import Entry, EntryStatus

# 终态：已完成 / 已取消（待办、进行中永不超龄）
_TERMINAL_STATUSES = {EntryStatus.DONE, EntryStatus.DROPPED}


def is_expiring(entry: Entry, scope: str, retention_days: int, now: datetime) -> bool:
    """判定条目是否为作用域内超龄的终态条目（运行时派生，不写入条目、不落盘）。

    本谓词是该判断的唯一判据，三个消费方（人读标记、`--json`
    输出投影、运行收尾清理）必须都经由它。条目须同时满足：
    终态（已完成/已取消）、有终态打点时间、打点时间已过 cutoff
    （`now - retention_days` 天）、且归属落在作用域内（含子域）。

    Args:
        entry: 待判定条目。
        scope: 作用域（含下级域）。
        retention_days: 终态后的保留天数；`<= 0` 视为禁用清理，恒为 False。
        now: 判定基准时间（本地朴素时间，与条目打点同为本地朴素时间）。

    Returns:
        是否超龄可清理。
    """
    if retention_days <= 0:
        return False
    if entry.status not in _TERMINAL_STATUSES:
        return False
    if entry.completed_at is None:
        return False
    cutoff = now - timedelta(days=retention_days)
    return entry.completed_at <= cutoff and is_within(entry.domain, scope)
