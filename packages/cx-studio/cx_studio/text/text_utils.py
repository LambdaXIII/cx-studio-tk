import re
from collections.abc import Callable, Iterable


def quick_search_chars(text: str, chars: str | Iterable[str]) -> bool:
    """通用文本引用域：判断文本中是否出现任一目标字符。"""
    for x in chars:
        if x in text:
            return True
    return False


def auto_quote(
    text: str,
    needs_quote: Callable[[str], bool] | str | Iterable[str] | bool | None = None,
) -> str:
    """通用文本引用域：按需为文本添加双引号（与路径域 quote_path、shell 域 escape_arg 区分）。"""
    needs_quote = needs_quote or [" "]  # type: ignore[assignment]  # or chain narrows to Iterable[str]
    quote = False
    if isinstance(needs_quote, Callable):
        quote = needs_quote(text)
    else:
        quote = quick_search_chars(text, needs_quote)  # type: ignore[arg-type]  # narrowed to str|Iterable[str] after Callable check
    return f'"{text}"' if quote else text


def auto_unquote(text: str, quotes="'\"") -> str:
    """通用文本引用域：去除文本首尾的引号（与路径域 quote_path、shell 域 escape_arg 区分）。"""
    for q in quotes:
        if text.startswith(q) and text.endswith(q):
            text = text[1:-1]
    return text


_random_string_letters = "abcdefghjkmnpqrstuwxyz0123456789"


def random_string(length=5):
    import random
    import string

    return "".join(random.choices(_random_string_letters + string.digits, k=length))


def auto_list_text(input: str | list[str] | None, sep=None) -> list[str]:
    if input is None:
        return []
    if isinstance(input, str):
        return input.split(sep or " ")
    return input


def auto_unwrap(t: str) -> str:
    t = re.sub(r"\r", "\n", t)
    t = re.sub(r"\n\s+", "\n", t)
    t = re.sub(r"\n+", lambda m: "\n" if len(m.group(0)) >= 2 else "", t)
    return t
