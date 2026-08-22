from pathlib import Path

from cx_studio.i18n import make_gettext, make_ngettext

_LOCALE_DIR = Path(__file__).resolve().parent.parent / "locales"
_ = make_gettext("cx-wealth", _LOCALE_DIR)
_ng = make_ngettext("cx-wealth", _LOCALE_DIR)

__all__ = ["_", "_ng"]
