"""cx-note 工具自持的 gettext 入口。

domain 为 `cx-note`，翻译文件位于本包 `i18n/locales/`。
源语言为简体中文——msgid 即中文，找不到 .mo 时 gettext 回退返回
msgid 本身，因此不提供 zh_CN 翻译文件。
"""

from pathlib import Path

from cx_studio.i18n import make_gettext, make_ngettext

_LOCALE_DIR = Path(__file__).resolve().parent / "locales"
_ = make_gettext("cx-note", _LOCALE_DIR)
_ng = make_ngettext("cx-note", _LOCALE_DIR)

__all__ = ["_", "_ng"]
