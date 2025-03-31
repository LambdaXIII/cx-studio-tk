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
