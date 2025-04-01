from collections.abc import Callable


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


_random_string_letters = "abcdefghjkmnpqrstuwxyz0123456789"


def random_string(length=5):
    import random
    import string

    return "".join(random.choices(_random_string_letters + string.digits, k=length))
