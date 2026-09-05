"""`NoteStore` —— 单 JSON 文件存储（ADR-0009：所有域共用一个 notes.json）。

纯 IO 层：不依赖 appenv，域语义只用到 `is_within` 边界判定；
清理时机由 application 层显式调用 `clean()` 决定（store 不感知配置）。
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from cx_note.common.domain import canonical, is_within
from cx_note.common.entry import Entry, EntryStatus, entry_from_json, entry_to_json
from cx_note.i18n import _
from cx_tools.app import SafeError

# 4 位小写 base36：1,679,616 空间，仅承担去碰撞、无安全语义，故用 random 而非 secrets
_ID_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_ID_LENGTH = 4


class NoteStore:
    """笔记条目存储。

    构造即加载：文件不存在 → 空条目集且不创建文件；存在但内容损坏
    （JSON 解析失败、条目缺键/非法、IO 错误）→ 抛 `SafeError`，
    **不静默清空**——数据安全优先，由 `CxNoteApp.__exit__` 承接为友好提示。

    Args:
        store_path: notes.json 的完整路径（调用方注入，如
            `ConfigManager("CxNote").get_file("notes.json")`）。
    """

    def __init__(self, store_path: Path):
        self._store_path = store_path
        self._entries: list[Entry] = []
        # canonical → 首见字面（无条目的域不存在，故只从条目域字面构建）
        self._literal_by_key: dict[str, str] = {}
        self._corrupted = False
        self._load()

    def _load(self) -> None:
        """读取存储文件；损坏时置损坏标记并立即抛出。

        status 容错：无法识别的状态 token（如 v1.1.0 存量数据中的
        `doing`）一律视为 `todo`，回存时自动合规——只放宽 status，
        时间戳非法仍按损坏处理。

        Raises:
            SafeError: 文件存在但无法完整解析。
        """
        if not self._store_path.exists():
            return
        corrupted = _("笔记存储已损坏: {path}").format(path=self._store_path)
        try:
            raw = json.loads(self._store_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            self._corrupted = True
            raise SafeError(corrupted) from e
        if not isinstance(raw, list):
            self._corrupted = True
            raise SafeError(corrupted)
        try:
            self._entries = [
                entry_from_json(self._normalize_status(item)) for item in raw
            ]
        except (KeyError, ValueError, TypeError) as e:
            self._corrupted = True
            raise SafeError(corrupted) from e
        for entry in self._entries:
            self._record_literal(entry.domain)

    @staticmethod
    def _normalize_status(item: dict) -> dict:
        """把无法识别的 status token 归一为 `todo`（加载容错，见 `_load`）。"""
        if not isinstance(item, dict):
            return item
        if item.get("status") not in {s.value for s in EntryStatus}:
            return {**item, "status": EntryStatus.TODO.value}
        return item

    def _record_literal(self, domain: str) -> str:
        """登记并返回域字面：canonical 命中已存字面时返回首见字面。"""
        key = canonical(domain)
        known = self._literal_by_key.get(key)
        if known is not None:
            return known
        self._literal_by_key[key] = domain
        return domain

    def _generate_id(self) -> str:
        """生成不与既有条目冲突的 4 位小写 base36 ID。"""
        existing = {e.id for e in self._entries}
        while True:
            candidate = "".join(random.choices(_ID_ALPHABET, k=_ID_LENGTH))
            if candidate not in existing:
                return candidate

    def _save(self) -> None:
        """原子重写存储文件（tmp + `os.replace`）。"""
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._store_path.with_name(self._store_path.name + ".tmp")
        payload = json.dumps(
            [entry_to_json(e) for e in self._entries], ensure_ascii=False, indent=2
        )
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, self._store_path)

    @property
    def corrupted(self) -> bool:
        """存储是否处于损坏状态（写路径据此拒写，避免覆盖残存数据）。"""
        return self._corrupted

    def entries(self) -> list[Entry]:
        """返回全部条目的副本（保持插入序）。"""
        return list(self._entries)

    def add(self, domain: str, content: str) -> Entry:
        """新增条目并立即落盘。

        content 中字面 `\\n` → 真实换行的转换在 application 层完成，
        store 不处理。域字面经 `_record_literal` 归一到首见字面。

        Args:
            domain: 归属域字面。
            content: 条目内容。

        Returns:
            新条目。

        Raises:
            SafeError: 存储处于损坏状态时拒绝写入。
        """
        if self._corrupted:
            raise SafeError(_("笔记存储已损坏: {path}").format(path=self._store_path))
        entry = Entry(
            id=self._generate_id(),
            domain=self._record_literal(domain),
            content=content,
            status=EntryStatus.TODO,
            created_at=datetime.now(),
            completed_at=None,
        )
        self._entries.append(entry)
        self._save()
        return entry

    def find_by_id(self, eid: str) -> Entry | None:
        """按 ID 精确查找（全库范围——ID 全局唯一）。"""
        return next((e for e in self._entries if e.id == eid), None)

    def find_by_text(self, current_domain: str, text: str) -> list[Entry]:
        """在可见域（当前域 + 下级域）内做 content 大小写不敏感子串匹配。"""
        needle = text.lower()
        return [
            e
            for e in self.visible_entries(current_domain)
            if needle in e.content.lower()
        ]

    def visible_entries(self, current_domain: str) -> list[Entry]:
        """返回当前域及其下级域内的全部条目（保持插入序）。"""
        return [e for e in self._entries if is_within(e.domain, current_domain)]

    def domain_entries(self, domain: str) -> list[Entry]:
        """返回指定域直属的全部条目（不含子域，保持插入序）。"""
        key = canonical(domain)
        return [e for e in self._entries if canonical(e.domain) == key]

    def transition(self, eid: str, status: EntryStatus) -> Entry | None:
        """把条目转移到目标状态并落盘。

        仅 `DONE` 打 `completed_at`；`TODO`/`PENDING` 一律清空打点。

        Args:
            eid: 目标条目 ID。
            status: 目标状态。

        Returns:
            转移后的新条目；ID 不存在时返回 None。
        """
        entry = self.find_by_id(eid)
        if entry is None:
            return None
        updated = Entry(
            id=entry.id,
            domain=entry.domain,
            content=entry.content,
            status=status,
            created_at=entry.created_at,
            completed_at=datetime.now() if status is EntryStatus.DONE else None,
        )
        self._entries[self._entries.index(entry)] = updated
        self._save()
        return updated

    def erase(self, eid: str) -> Entry | None:
        """删除单条条目并返回被删条目；ID 不存在时返回 None。"""
        entry = self.find_by_id(eid)
        if entry is None:
            return None
        self._entries.remove(entry)
        self._save()
        return entry

    def clear_domain(self, domain: str) -> list[Entry]:
        """清空指定域直属的全部条目（不含子域）并落盘。

        Args:
            domain: 目标域字面。

        Returns:
            被清除的条目列表；域内无条目时不落盘、返回空列表。

        Raises:
            SafeError: 存储处于损坏状态时拒绝写入。
        """
        if self._corrupted:
            raise SafeError(_("笔记存储已损坏: {path}").format(path=self._store_path))
        doomed = self.domain_entries(domain)
        if not doomed:
            return []
        for entry in doomed:
            self._entries.remove(entry)
        self._save()
        key = canonical(domain)
        if not any(canonical(e.domain) == key for e in self._entries):
            self._literal_by_key.pop(key, None)
        return doomed

    def clean(self, domain: str, retention_days: int) -> list[Entry]:
        """清理指定域内超龄的已完成条目。

        `retention_days <= 0` 视为禁用，直接返回空列表；未完成条目
        永不参与清理。

        Args:
            domain: 清理作用域（含下级域）。
            retention_days: 完成后的保留天数。

        Returns:
            被清理的条目列表（无清理发生时不落盘、返回空列表）。
        """
        if retention_days <= 0:
            return []
        cutoff = datetime.now() - timedelta(days=retention_days)
        doomed = [
            e
            for e in self._entries
            if e.status is EntryStatus.DONE
            and e.completed_at is not None
            and e.completed_at <= cutoff
            and is_within(e.domain, domain)
        ]
        if not doomed:
            return []
        for entry in doomed:
            self._entries.remove(entry)
        self._save()
        return doomed
