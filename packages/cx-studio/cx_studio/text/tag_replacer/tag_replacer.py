"""TagReplacer —— 模板标签占位符替换器。

按「标签键 → provider」注册表（服务定位模式）把文本中的占位符展开为
provider 提供的值。占位符形态由 TagPattern 定义（默认 ${key:param}）；
常用 provider 见 path_info_provider / standard_folder_provider 模块。
"""

import re
from collections.abc import Callable

from .tag_pattern import TagPattern


class TagReplacer:
    """按标签键注册/查询/移除 provider 并替换占位符的服务定位器。

    注册与替换分离：install_provider() 注册、get_provider() 查询、
    remove_provider() 移除；replace() 依 TagPattern 扫描文本，为每个
    命中的占位符查找对应 provider 求值替换。生命周期约定：

    - 占位符的键未注册 → 保留原文，不替换
    - provider 为常量字符串 → 直接作为替换结果
    - provider 为 Callable → 占位符携带参数时以参数为入参调用，
      否则无参调用；返回 falsy（None/空串等）时保留原占位符
    - install/remove 均返回 self，可链式调用

    Args:
        tag_pattern: 自定义占位符模式；None 时使用 TagPattern 默认模式
            （${key} / ${key:param}）。
    """

    def __init__(self, tag_pattern: TagPattern | None = None):
        self.__tag_providers: dict[str, Callable | str] = {}
        self.__tag_pattern = tag_pattern or TagPattern()

    def install_provider(self, key: str, provider: Callable | str):
        """注册标签键对应的 provider。

        Args:
            key: 占位符键（默认模式即 ${key:param} 中的 key）。
            provider: 常量字符串或 Callable。Callable 的调用约定见
                类 docstring。

        Returns:
            self，便于链式注册多个 provider。
        """
        self.__tag_providers[key] = provider
        return self

    def get_provider(self, key: str) -> Callable | str | None:
        """查询已注册的 provider。

        Args:
            key: 占位符键。

        Returns:
            该键注册的 provider（字符串或 Callable）；未注册返回 None。
        """
        return self.__tag_providers.get(key)

    def remove_provider(self, key: str):
        """移除已注册的 provider。

        Args:
            key: 占位符键。

        Returns:
            self，便于链式调用。

        Raises:
            KeyError: 该键尚未注册。
        """
        self.__tag_providers.pop(key)
        return self

    def __provide(self, match: re.Match) -> str:
        key, param = self.__tag_pattern.parse(match)
        if not key in self.__tag_providers:
            return match.group(0)

        provider = self.__tag_providers[key]
        if isinstance(provider, Callable):
            result = provider(param) if param else provider()
            return str(result) if result else match.group(0)

        return str(provider)

    def replace(self, source: str) -> str:
        """替换文本中所有可识别的占位符。

        Args:
            source: 含占位符的源文本。

        Returns:
            替换完成的文本；未注册键或 provider 返回 falsy 的占位符
            保留原文。
        """
        return re.sub(self.__tag_pattern.regex_pattern, self.__provide, source)
