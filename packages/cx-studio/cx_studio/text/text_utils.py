"""text_utils：通用文本处理工具函数集。

提供若干彼此独立的文本小工具：
- quick_search_chars / auto_quote / auto_unquote：文本引用域——
  探测目标字符并按需加/去引号（与路径域的 quote_path、shell 域的
  escape_arg 相区分，见各自 docstring）
- random_string：随机字符串生成
- auto_list_text：把 None/str/list 输入归一到字符串列表
- auto_unwrap：清除换行并把多行文本折叠为单行
"""

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
    """生成随机字符串。

    Args:
        length: 结果字符串长度，默认 5。

    Returns:
        随机字符串。字符取自小写字母与十进制数字组成的字符池，
        其中字母已剔除易混淆的 i/l/o/v。
    """
    import random
    import string

    return "".join(random.choices(_random_string_letters + string.digits, k=length))


def auto_list_text(input: str | list[str] | None, sep=None) -> list[str]:
    """把输入归一为字符串列表。

    Args:
        input: 输入内容。None 返回空列表；str 按 sep 拆分；
            list[str] 原样返回。
        sep: 拆分分隔符；None（默认）或空串时按单个空格字符 " "
            拆分。str.split 语义下连续多个空格会拆出空字符串元素。

    Returns:
        拆分/转换后的字符串列表。
    """
    if input is None:
        return []
    if isinstance(input, str):
        return input.split(sep or " ")
    return input


def auto_unwrap(t: str) -> str:
    """清除换行并把多行文本折叠为单行。

    先把 \\r、\\r\\n 统一为 \\n，移除所有换行并清除换行后的行首空白；
    空行分隔的段落换行同样被删除，不保留段落结构。

    Args:
        t: 原始文本，典型为跨行的字符串字面量。

    Returns:
        不含换行符的折叠文本。
    """
    t = re.sub(r"\r", "\n", t)
    t = re.sub(r"\n\s+", "\n", t)
    t = re.sub(r"\n+", lambda m: "\n" if len(m.group(0)) >= 2 else "", t)
    return t
