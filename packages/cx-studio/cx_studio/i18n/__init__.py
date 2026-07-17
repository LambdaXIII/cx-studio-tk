from __future__ import annotations

import gettext
import os
from functools import cache
from pathlib import Path

_LOCALE_DIR = Path(__file__).resolve().parent.parent / "locales"


@cache
def _load_translation(domain: str, locale_dir: str | Path) -> gettext.NullTranslations:
    return gettext.translation(domain, localedir=str(locale_dir), fallback=True)


def make_gettext(domain: str, locale_dir: str | Path):
    """返回该(domain, locale_dir)的 `_()` 函数。"""
    return _load_translation(domain, locale_dir).gettext


def make_ngettext(domain: str, locale_dir: str | Path):
    """返回该(domain, locale_dir)的 `ngettext()` 函数，支持复数。"""
    return _load_translation(domain, locale_dir).ngettext


def detect_locale() -> str:
    """检测用户 locale，遵循 GNU gettext 标准顺序。

    按 LANGUAGE → LC_ALL → LC_MESSAGES → LANG 顺序检测环境变量。
    LANGUAGE 支持 ":" 分隔的列表（如 "en_US:zh_CN"），取第一项。
    全部缺失时回退到 'zh_CN'。
    """
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val:
            first = val.split(":", 1)[0]
            return first.split(".")[0].replace("-", "_")
    return "zh_CN"


def load_localized_text(
    package: str,
    basename: str,
    locale: str | None = None,
    encoding: str = "utf-8",
) -> str:
    """从包资源中加载本地化文本文件。

    加载顺序（第一个存在的作为结果）：
    1. <stem>.<locale><ext>  （如果 locale 非 'zh_CN'）
    2. <basename>            （回退到源语言）

    文件名格式：help.md（中文源语言）、help.en_US.md（英文）、help.ja_JP.md（日文）等。
    """
    import importlib.resources

    lang = locale or detect_locale()
    if lang != "zh_CN":
        dot = basename.rfind(".")
        if dot != -1:
            stem = basename[:dot]
            ext = basename[dot:]
        else:
            stem = basename
            ext = ""
        localized_name = f"{stem}.{lang}{ext}"
        try:
            return importlib.resources.read_text(
                package, localized_name, encoding=encoding
            )
        except (FileNotFoundError, ModuleNotFoundError):
            pass

    return importlib.resources.read_text(package, basename, encoding=encoding)


# cx-studio 包自己的翻译函数
_ = make_gettext("cx-studio", _LOCALE_DIR)
_ng = make_ngettext("cx-studio", _LOCALE_DIR)

__all__ = [
    "_",
    "_ng",
    "make_gettext",
    "make_ngettext",
    "detect_locale",
    "load_localized_text",
]
