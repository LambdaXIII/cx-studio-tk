from argparse import ArgumentParser
from dataclasses import dataclass
from collections.abc import Sequence
from typing import Literal
from xml.etree.ElementInclude import include

from cx_studio.utils.cx_textutils import auto_quote
from cx_wealth import WealthHelp
from cx_wealth import rich_types as r
import importlib.resources


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
class AppContext:
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

    @classmethod
    def load(cls, arguments: Sequence[str] | None = None):
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


class MSHelp(WealthHelp):
    def __init__(self):
        super().__init__(
            prog="MediaScout",
            description=(
                "解析时间线、元数据表格等项目文件，从中提取包含的文件路径。支持干净的输出流或输出到文件。"
                "目前可以解析的类型包括：EDL表、FCP7 经典XML、FCP XML文件或包、Davinci Resolve 媒体池元数据、纯文本路径列表等。"
            ),
        )
        p_group = self.add_group("文件输入", "输入需要解析的文件，可以一次解析多个。")
        p_group.add_action(
            "inputs", metavar="FILE", nargs="*", description="需要解析的文件"
        )

        o_group = self.add_group("选项", "对结果进行处理的若干选项")
        o_group.add_action(
            "-i",
            "--include",
            metavar="DIR",
            nargs="**",
            description="指定用于搜索无路径文件名的文件夹",
        )
        o_group.add_action("-e", "--existed-only", description="仅输出已存在的文件路径")
        o_group.add_action("--allow-duplicated", description="允许重复输出文件路径")
        o_group.add_action("--auto-resolve", description="自动解析并整理文件路径")
        o_group.add_action(
            "-q",
            "--quote-mode",
            metavar="auto|force|excape|none",
            description="指定对于包含空格的路径的处理方式",
        )
        o_group.add_action(
            "-o", "--output", metavar="OUTPUT", description="将文件列表保存到目标文件"
        )

        x_group = self.add_group("其它")
        x_group.add_action("-d", "--debug", description="开启调试模式")
        x_group.add_action("-h", "--help", description="显示帮助信息")
        x_group.add_action(
            "--tutorial", "--full-help", description="显示完整的帮助信息"
        )

        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

    @staticmethod
    def show_help(console: r.Console):
        console.print(MSHelp())

    @staticmethod
    def show_full_help(console: r.Console):
        md = importlib.resources.read_text("media_scout", "help.md")
        content = r.Markdown(md, style="default")
        panel = r.Panel(
            content,
            title="MediaScout 教程",
            title_align="left",
            style="bright_black",
            width=90,
        )
        console.print(r.Align.center(panel))
