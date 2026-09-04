"""TagPattern —— 模板占位符的正则模式定义与解析。

以编译后的正则描述占位符形态（默认 ${key} / ${key:param}），并提供
parse() 把一次匹配解析为 (key, param) 二元组，供 TagReplacer 在
替换时取用。
"""

import re


class TagPattern:
    """占位符标签的正则模式，负责匹配并解析 ${key:param} 形态的占位符。

    默认模式匹配 ${key} 与 ${key:param} 两种形态（键与参数均为单词
    字符 \\w，参数可连同冒号一起省略）；传入自定义 pattern 时必须显式
    命名两个捕获组为 key 与 param，否则 parse() 无法按组名取值。

    Attributes:
        regex_pattern: 编译后的正则对象（re.Pattern），可直接传给
            re.sub / re.match 等。

    Args:
        pattern: 自定义正则（字符串或已编译的 re.Pattern）；
            None 时使用默认模式。
    """

    def __init__(self, pattern: str | None | re.Pattern = None):
        self.__pattern = (
            re.compile(pattern)
            if pattern
            else re.compile(r"\$\{(?P<key>\w+):?(?P<param>\w+)?\}")
        )

    @property
    def regex_pattern(self):
        """返回编译后的占位符正则对象。

        Returns:
            re.Pattern：构造时传入的 pattern 的编译结果；未传时为默认
            模式的编译结果。
        """
        return self.__pattern

    def parse(self, match: re.Match) -> tuple[str, str]:
        """从一次匹配中提取占位符的键与参数。

        Args:
            match: 由本模式的 regex_pattern 匹配产生的对象，须含 key
                与 param 两个命名组（parse 按组名取值）。

        Returns:
            (key, param) 二元组。param 为占位符参数部分的字符串；
            参数组可省略，省略时其值为 None（与签名标注的 str 不同，
            系 re 可选组的运行语义）。
        """
        return match.group("key"), match.group("param")
