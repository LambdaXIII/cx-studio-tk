"""MediaScout 命令行上下文与参数解析。"""

from argparse import ArgumentParser
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from cx_tools.app import IAppContext


class ArgParser(ArgumentParser):
    def __init__(self):
        super().__init__(
            prog="MediaScout",
            description="MediaScout is a tool for inspecting media files.",
            epilog="",
            add_help=False,
        )

        self.add_argument("inputs", nargs="*", metavar="INPUTS")
        self.add_argument("-i", "--include", dest="includes", nargs="*")
        self.add_argument(
            "-e",
            "--existed-only",
            dest="existed_only",
            default=False,
            action="store_true",
        )
        self.add_argument(
            "-o",
            "--output",
            action="store",
            dest="output",
            metavar="OUTPUT",
            default=None,
        )
        self.add_argument(
            "--allow-duplicated",
            action="store_true",
            default=False,
            dest="allow_duplicated",
        )
        self.add_argument(
            "-q",
            "--quote-mode",
            default="none",
            choices=["auto", "force", "escape", "none"],
            dest="quote_mode",
        )
        self.add_argument(
            "--auto-resolve", action="store_true", default=False, dest="auto_resolve"
        )
        self.add_argument(
            "-d", "--debug", action="store_true", default=False, dest="debug_mode"
        )
        self.add_argument(
            "-h", "--help", action="store_true", default=False, dest="show_help"
        )
        self.add_argument(
            "--tutorial",
            "--full-help",
            action="store_true",
            default=False,
            dest="show_full_help",
        )


@dataclass
class MediaScoutContext(IAppContext):
    """MediaScout 命令行上下文。

    持有 argparse 解析后的参数，继承 IAppContext 的 temp_dir 能力和生命周期管理。
    """

    inputs: list[str]
    includes: list[str]
    output: str | None
    allow_duplicated: bool
    auto_resolve: bool
    existed_only: bool
    quote_mode: Literal["auto", "force", "escape", "none"]
    debug_mode: bool
    show_help: bool
    show_full_help: bool

    def __post_init__(self) -> None:
        """初始化 IAppContext 的 _temp_dir 等基础设施。"""
        super().__init__()

    @classmethod
    def load(cls, arguments: Sequence[str] | None = None):
        """从命令行参数构造上下文。"""
        parser = ArgParser()
        args = parser.parse_args(arguments)
        return cls(
            inputs=args.inputs or [],
            includes=args.includes or [],
            output=args.output,
            allow_duplicated=args.allow_duplicated,
            auto_resolve=args.auto_resolve,
            existed_only=args.existed_only,
            quote_mode=args.quote_mode,
            debug_mode=args.debug_mode,
            show_help=args.show_help,
            show_full_help=args.show_full_help,
        )

    def __rich_detail__(self):
        yield from self.__dict__.items()
