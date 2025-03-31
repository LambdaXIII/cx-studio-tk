import re


class TagPattern:
    """
    A class to represent and work with a tag pattern for parsing strings.

    The pattern must explicitlly name the group of regex as 'key' and 'param'.

    Attributes:
        regex_pattern (str): The regular expression pattern used to match tags.
    Methods:
        parse(match: re.Match) -> tuple[str, str]:
            Parses a regex match object and extracts the key and parameter from the tag.
    """

    def __init__(self, pattern=None):
        self.__pattern = pattern or r"\$\{(?P<key>\w+):?(?P<param>\w+)?\}"

    @property
    def regex_pattern(self):
        return self.__pattern

    def parse(self, match: re.Match) -> tuple[str, str]:
        return match.group("key"), match.group("param")
