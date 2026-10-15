"""`NoteStore` —— 单 JSON 文件存储（所有域共用一个 notes.json）。

纯 IO 层：不依赖 appenv，域语义只用到 `is_within` 边界判定。

工作集 + 显式落盘模型：构造时一次性把全量条目读进内存（工作集），
所有变更方法只改工作集、不碰磁盘；持久化由调用方在运行收尾显式
调用 `flush()`——一次运行至多落盘一次，工作集与读盘结果一致时
不写盘。保留期与清理作用域的判断属于 application 层（判据见
`cx_note.common.expiry.is_expiring`），store 不感知配置。
"""

import json
import os
import random
from datetime import datetime
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
        # 脏标记：工作集相对读盘结果有实际变更时为 True，flush 落盘后复位
        self._dirty = False
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

    def flush(self) -> bool:
        """工作集有变更时原子重写存储文件（tmp + `os.replace`），一次运行至多落盘一次。

        工作集与读盘结果一致时不写盘（脏标记为 False 直接返回）。

        Returns:
            是否实际落盘：写入成功返回 True，未写返回 False。
        """
        if not self._dirty:
            return False
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._store_path.with_name(self._store_path.name + ".tmp")
        payload = json.dumps(
            [entry_to_json(e) for e in self._entries], ensure_ascii=False, indent=2
        )
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, self._store_path)
        self._dirty = False
        return True

    @property
    def corrupted(self) -> bool:
        """存储是否处于损坏状态（写路径据此拒写，避免覆盖残存数据）。"""
        return self._corrupted

    def entries(self) -> list[Entry]:
        """返回全部条目的副本（保持插入序）。"""
        return list(self._entries)

    def add(self, domain: str, content: str) -> Entry:
        """新增条目（仅改工作集，落盘由 `flush()` 显式触发）。

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
        self._dirty = True
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
        """把条目转移到目标状态（仅改工作集，落盘由 `flush()` 显式触发）。

        终态打点：目标状态为终态（`DONE`/`DROPPED`）时记录
        `completed_at`；离开终态（`TODO`/`PENDING`）时清空。

        Args:
            eid: 目标条目 ID。
            status: 目标状态。

        Returns:
            转移后的新条目；ID 不存在时返回 None。
        """
        entry = self.find_by_id(eid)
        if entry is None:
            return None
        is_terminal = status in {EntryStatus.DONE, EntryStatus.DROPPED}
        updated = Entry(
            id=entry.id,
            domain=entry.domain,
            content=entry.content,
            status=status,
            created_at=entry.created_at,
            completed_at=datetime.now() if is_terminal else None,
        )
        self._entries[self._entries.index(entry)] = updated
        self._dirty = True
        return updated

    def take(self, eid: str) -> Entry | None:
        """取出单条条目并从工作集移除；ID 不存在时返回 None。

        仅改工作集，不落盘（落盘由 `flush()` 显式触发）。

        Args:
            eid: 目标条目 ID。

        Returns:
            被取出的条目；ID 不存在时返回 None。
        """
        entry = self.find_by_id(eid)
        if entry is None:
            return None
        self._entries.remove(entry)
        self._dirty = True
        return entry

    def set_content(self, eid: str, content: str) -> Entry | None:
        """覆盖条目的内容文本（`edit` 用），其余字段不动。

        仅改工作集，不落盘（落盘由 `flush()` 显式触发）。
        新内容与原内容相同时仍返回该条目（调用方据此计一次变更），
        但不置脏——工作集与读盘结果一致时不写盘。

        Args:
            eid: 目标条目 ID。
            content: 覆盖后的内容。

        Returns:
            覆盖后的新条目（内容未变时为原条目）；ID 不存在时返回 None。
        """
        entry = self.find_by_id(eid)
        if entry is None:
            return None
        if entry.content == content:
            return entry
        updated = Entry(
            id=entry.id,
            domain=entry.domain,
            content=content,
            status=entry.status,
            created_at=entry.created_at,
            completed_at=entry.completed_at,
        )
        self._entries[self._entries.index(entry)] = updated
        self._dirty = True
        return updated

    def take_domain(self, domain: str) -> list[Entry]:
        """取出指定域直属的全部条目（不含子域）并从工作集移除。

        仅改工作集，不落盘（落盘由 `flush()` 显式触发）。
        域被取空时同步注销其域字面登记——无条目的域不留字面登记。

        Args:
            domain: 目标域字面。

        Returns:
            被取出的条目列表；域内无条目时返回空列表、工作集不变。

        Raises:
            SafeError: 存储处于损坏状态时拒绝操作。
        """
        if self._corrupted:
            raise SafeError(_("笔记存储已损坏: {path}").format(path=self._store_path))
        doomed = self.domain_entries(domain)
        if not doomed:
            return []
        for entry in doomed:
            self._entries.remove(entry)
        self._dirty = True
        key = canonical(domain)
        if not any(canonical(e.domain) == key for e in self._entries):
            self._literal_by_key.pop(key, None)
        return doomed

    def take_many(self, entries: list[Entry]) -> list[Entry]:
        """按 ID 批量取出条目并从工作集移除（运行收尾清理用）。

        仅改工作集，不落盘（落盘由 `flush()` 显式触发）。
        域被取空时同步注销其域字面登记——无条目的域不留字面登记。
        未命中工作集的 ID（重复或不存在）直接忽略。

        Args:
            entries: 待取出的条目列表，只按其 ID 匹配工作集。

        Returns:
            实际从工作集取出的条目（保持工作集内原有顺序）；
            全部未命中时返回空列表、工作集不变。
        """
        wanted = {e.id for e in entries}
        if not wanted:
            return []
        doomed = [e for e in self._entries if e.id in wanted]
        if not doomed:
            return []
        doomed_ids = {e.id for e in doomed}
        self._entries = [e for e in self._entries if e.id not in doomed_ids]
        self._dirty = True
        for key in {canonical(e.domain) for e in doomed}:
            if not any(canonical(e.domain) == key for e in self._entries):
                self._literal_by_key.pop(key, None)
        return doomed
