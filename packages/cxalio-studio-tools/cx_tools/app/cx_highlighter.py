from rich.highlighter import RegexHighlighter


class CxHighlighter(RegexHighlighter):
    DEFAULT_STYLES = {
        "cx.info": "dim italic grey",
        "cx.debug": "dim cyan",
        "cx.warning": "bold yellow",
        "cx.error": "bold red",
        "cx.success": "bold green",
        "cx.number": "bold yellow",
        "cx.brackets": "bold dim",
        "cx.quotes": "cyan",
        "cx.filepath": "bold magenta",
    }
    base_style = "cx."
    highlights = [
        r"(?P<number>\b\d+(?:\.\d+)?\b)",  # 数字
        r"(?P<brackets>\(.*?\))",  # 括号括起的
        r"(?P<quotes>\".*?\"|\'.*?\')",  # 引号引用的
        r"(?P<filepath>[A-Za-z]:[\\/][^:*?\"<>|\n]*)",  # Windows 文件路径
        r"(?P<filepath>[\\/][^:*?\"<>|\n]*)",  # Unix 文件路径
    ]
