from .cx_tagpattern import TagPattern
import re


class TagReplacer:

    def __init__(self, tag_pattern: TagPattern = None):
        self.__tag_providers = {}
        self.__tag_pattern = tag_pattern or TagPattern()

    def install_provider(self, key: str, provider: callable | str):
        self.__tag_providers[key] = provider
        return self

    def get_provider(self, key: str) -> callable | str:
        return self.__tag_providers.get(key)

    def remove_provider(self, key: str):
        self.__tag_providers.pop(key)
        return self

    def __provide(self, match: re.Match) -> str:
        key, param = self.__tag_pattern.parse(match)
        if not key in self.__tag_providers:
            return match.group(0)

        provider = self.__tag_providers[key]
        if isinstance(provider, callable):
            result = provider(param) if param else provider()
            return str(result)

        return str(provider)

    def replace(self, source: str) -> str:
        return re.sub(self.__tag_pattern.regex_pattern, self.__provide, source)
