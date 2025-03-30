import re


class TagPattern:

    def __init__(self, pattern=None):
        self.__pattern = pattern or r"\$\{(?P<key>\w+):?(?P<param>\w+)?\}"

    @property
    def regex_pattern(self):
        return self.__pattern

    def parse(self, match: re.Match) -> tuple[str, str]:
        return match.group("key"), match.group("param")
