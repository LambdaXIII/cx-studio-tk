from __future__ import annotations
from argparse import ArgumentParser
from collections.abc import Sequence, Generator
from typing import Any, Literal

from cx_tools.i18n import _


class AppContext:
    def __init__(self, **kwargs: Any) -> None:
        self.inputs: list[str] = []
        self.script_output: str | None = None
        self.pretending_mode: bool = False
        self.debug_mode: bool = False
        self.sort_mode: Literal["source", "preset", "target", "x"] = "x"
        self.continue_mode: bool = False
        self.generate: bool = False
        self.save_script: str | None = None
        self.show_full_help: bool = False
        self.force_overwrite: bool = False
        self.force_no_overwrite: bool = False
        self.output_dir: str | None = None
        self.show_help: bool = False
        self.max_workers: int = 1

        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    def __rich_repr__(self) -> Generator[tuple[str, Any], None, None]:
        yield from self.__dict__.items()

    @staticmethod
    def __make_parser() -> ArgumentParser:
        parser = ArgumentParser(
            # prog="MediaKiller",
            description=_("MediaKiller 是一个命令行多媒体文件批量处理工具。"),
            # formatter_class=RichHelpFormatter,
            epilog=_("—— 来自 Cxalio 工作室工具集。"),
            add_help=False,
        )

        parser.add_argument(
            "inputs",
            help=_("多个需要处理的文件路径[dim]（源文件或配置文件）"),
            nargs="*",
            metavar=_("输入文件"),
        )

        parser.add_argument(
            "-g",
            "--generate",
            help=_("生成新的预设文件示例"),
            action="store_true",
            default=False,
            dest="generate",
        )
        parser.add_argument("--save-script", "-s", help=_("将转码任务编写为脚本"))
        parser.add_argument(
            "-j",
            "--jobs",
            "--max-workers",
            help=_("指定最大工作线程数"),
            type=int,
            default=1,
            dest="max_workers",
            metavar=_("线程数"),
        )
        parser.add_argument(
            "-c",
            "--continue",
            action="store_true",
            help=_("重新加载上次运行的任务"),
            dest="continue_mode",
        )

        parser.add_argument(
            "--output",
            "-o",
            help=_("指定一个输出目录"),
            metavar=_("输出目录"),
            default=None,
            dest="output_dir",
        )
        parser.add_argument(
            "--sort",
            help=_("指定任务排序方式"),
            choices=["source", "preset", "target", "x"],
            default="x",
            metavar=_("排序方式代码"),
            dest="sort_mode",
        )

        parser.add_argument(
            "--overwrite",
            "-y",
            help=_("强制覆盖所有输出文件"),
            action="store_true",
            default=False,
            dest="force_overwrite",
        )

        parser.add_argument(
            "--no-overwrite",
            "-n",
            help=_("强制启用安全模式（不覆盖已有文件）"),
            action="store_true",
            default=False,
            dest="force_no_overwrite",
        )

        parser.add_argument(
            "-h",
            "--help",
            # action="help",
            help=_("显示此帮助信息"),
            dest="show_help",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--tutorial",
            "--full-help",
            action="store_true",
            help=_("显示详细教程"),
            dest="show_full_help",
        )

        parser.add_argument(
            "-p",
            "--pretend",
            help=_("以[italic dim]假装模式[/]模拟运行 :)"),
            action="store_true",
            dest="pretending_mode",
        )
        parser.add_argument(
            "-d",
            "--debug",
            help=_("显示调试信息"),
            action="store_true",
            dest="debug_mode",
        )

        return parser

    @classmethod
    def from_arguments(cls, arguments: Sequence[str] | None = None) -> AppContext:
        parser = cls.__make_parser()
        args = parser.parse_args(arguments)
        return cls(**vars(args))
