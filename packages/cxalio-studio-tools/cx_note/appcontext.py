"""CxNote 应用上下文。

`CxNoteContext` 是命令行参数解析后的值对象，采用 `from_arguments()`
工厂方法构造，并通过 kwargs 白名单完成字段赋值。
"""

from argparse import ArgumentParser
from collections.abc import Generator, Sequence
from typing import Any

from cx_note.i18n import _
from cx_tools.app import IAppContext

# 动词表——argparse choices 与运行时分派共用，防止两处漂移。
VERBS = ["add", "list", "done", "doing", "reset", "clear", "clean", "config"]


class CxNoteContext(IAppContext):
    """CxNote 命令行上下文。

    Fields:
        verb: 要执行的动词，缺省为 `list`。
        argument: 动词参数——add 为条目内容；done/doing/reset/clear 为
            ID 或文本片段；config 为要设置的 retention_days 整数字符串。
        domain_param: `-p/--path` 给出的域字面。
        global_flag: 是否指定 `-g/--global`（在根域操作）。
        json_output: 是否指定 `--json`（stdout 纯净 JSON 输出）。
        full: 是否指定 `--full`（列表展开下级域条目，并扩大 `--json`
            范围为当前域 + 全部下级域）。
        debug_mode: debug 模式开关。
        show_help: 帮助开关（当前帮助走 argparse 默认行为，字段保留）。
        show_full_help: 完整教程开关（预留，暂未启用）。
    """

    def __init__(self, **kwargs: Any):
        """用 kwargs 白名单初始化上下文字段。"""
        super().__init__()
        self.verb: str = "list"
        self.argument: str | None = None
        self.domain_param: str | None = None
        self.global_flag: bool = False
        self.json_output: bool = False
        self.full: bool = False
        self.debug_mode: bool = False
        self.show_help: bool = False
        self.show_full_help: bool = False

        for k, v in kwargs.items():
            if k in self.__dict__:
                setattr(self, k, v)

    def __rich_repr__(self) -> Generator[tuple[str, Any], None, None]:
        """返回所有字段的 `(name, value)` 表示，用于 debug 详情面板。"""
        yield from ((k, v) for k, v in self.__dict__.items() if not k.startswith("_"))

    @classmethod
    def from_arguments(cls, arguments: Sequence[str] | None = None) -> "CxNoteContext":
        """从命令行参数构造上下文。

        Args:
            arguments: 要解析的字符串序列；None 时使用 `sys.argv[1:]`。

        Returns:
            解析后的 `CxNoteContext` 实例。
        """
        parser = cls.__make_parser()
        args = parser.parse_args(arguments)
        return cls(**vars(args))

    @staticmethod
    def __make_parser() -> ArgumentParser:
        """构建 CxNote 的 argparse 解析器。"""
        parser = ArgumentParser(
            description=_("cxnote —— 终端里的快速便签。"),
        )
        parser.add_argument(
            "verb",
            nargs="?",
            default="list",
            choices=VERBS,
            help=_("要执行的动作，缺省为 list"),
        )
        parser.add_argument(
            "argument",
            nargs="?",
            help=_(
                "动词参数：add 为条目内容；done/doing/reset/clear 为 ID 或文本片段；"
                "config 为保留天数整数"
            ),
        )
        parser.add_argument(
            "-p",
            "--path",
            dest="domain_param",
            help=_("指定域字面（以 / 开头为绝对域，否则相对当前域）"),
        )
        parser.add_argument(
            "-g",
            "--global",
            dest="global_flag",
            action="store_true",
            help=_("在根域操作"),
        )
        parser.add_argument(
            "--json",
            dest="json_output",
            action="store_true",
            help=_("向 stdout 输出纯净 JSON"),
        )
        parser.add_argument(
            "--full",
            dest="full",
            action="store_true",
            help=_("同时显示下级域的条目"),
        )
        parser.add_argument(
            "-d",
            "--debug",
            dest="debug_mode",
            action="store_true",
            help=_("开启 debug 模式"),
        )
        return parser
