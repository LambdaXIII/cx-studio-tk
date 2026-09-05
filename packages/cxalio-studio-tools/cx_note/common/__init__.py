"""cx_note 通用能力面。

承载域解析、条目模型与单 JSON 存储。
全部为不依赖 appenv 的纯逻辑；组件层与 application 层从这里取用。
"""

from .domain import (
    ROOT_DOMAIN,
    canonical,
    derive_from_cwd,
    is_within,
    join_domain,
    normalize_domain_literal,
    resolve_domain,
    subdomains_of,
)
from .entry import Entry, EntryStatus, entry_from_json, entry_to_json
from .note_store import NoteStore

__all__ = [
    "ROOT_DOMAIN",
    "Entry",
    "EntryStatus",
    "NoteStore",
    "canonical",
    "derive_from_cwd",
    "entry_from_json",
    "entry_to_json",
    "is_within",
    "join_domain",
    "normalize_domain_literal",
    "resolve_domain",
    "subdomains_of",
]
