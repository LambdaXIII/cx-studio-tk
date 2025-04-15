from collections.abc import Callable
import re


def auto_quote(text: str, needs_quote=None) -> str:
    needs_quote = needs_quote or [" "]
    quote = False
    if isinstance(needs_quote, Callable):
        quote = needs_quote(text)
    else:
        for x in needs_quote:
            if x in text:
                quote = True
                break
    return f'"{text}"' if quote else text


def auto_unquote(text: str, quotes="'\"") -> str:
    for q in quotes:
        if text.startswith(q) and text.endswith(q):
            text = text[1:-1]
    return text


_random_string_letters = "abcdefghjkmnpqrstuwxyz0123456789"


def random_string(length=5):
    import random
    import string

    return "".join(random.choices(_random_string_letters + string.digits, k=length))


def auto_list(input: str | list[str] | None, sep=None) -> list[str]:
    if input is None:
        return []
    if isinstance(input, str):
        return input.split(sep or " ")
    return input


def unwrap(t: str) -> str:
    t = re.sub(r"\r", "\n", t)
    t = re.sub(r"\n\s+", "\n", t)
    t = re.sub(r"\n+", lambda m: "\n" if len(m.group(0)) >= 2 else "", t)
    return t
