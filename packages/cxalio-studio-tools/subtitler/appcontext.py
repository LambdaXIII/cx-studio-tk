"""Subtitler 应用上下文。

`SubtitlerContext` 是命令行参数解析后的值对象，采用 `from_arguments()` 工厂
方法构造，并通过 kwargs 白名单完成字段赋值。工具是单动作的：位置参数恰为
输入与输出两个文件路径，转换时的格式按扩展名识别。
"""

from argparse import ArgumentParser
from collections.abc import Generator, Sequence
from pathlib import Path
from typing import Any

from cx_tools.app import IAppContext

from .i18n import _


class SubtitlerContext(IAppContext):
    """Subtitler 命令行上下文。

    Fields:
        input: 输入文件路径；`-h`/`--tutorial` 路径下为 None。
        output: 输出文件路径；`-h`/`--tutorial` 路径下为 None。
        debug_mode: debug 模式开关。
        show_help: 是否指定 `-h`（分组帮助）。
        show_full_help: 是否指定 `--tutorial`（完整教程）。
    """

    def __init__(self, **kwargs: Any):
        """用 kwargs 白名单初始化上下文字段。"""
        super().__init__()
        self.input: Path | None = None
        self.output: Path | None = None
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
    def from_arguments(
        cls, arguments: Sequence[str] | None = None
    ) -> "SubtitlerContext":
        """从命令行参数构造上下文。

        Args:
            arguments: 要解析的字符串序列；None 时使用 `sys.argv[1:]`。

        Returns:
            解析后的 `SubtitlerContext` 实例。
        """
        parser = cls.__make_parser()
        args = parser.parse_args(arguments)
        # 帮助路径不要求位置参数；正常转换路径缺少 INPUT/OUTPUT 时报解析错误。
        if not (args.show_help or args.show_full_help) and (
            args.input is None or args.output is None
        ):
            parser.error(_("需要恰好两个位置参数：INPUT 与 OUTPUT。"))
        return cls(**vars(args))

    @staticmethod
    def __make_parser() -> ArgumentParser:
        """构建 Subtitler 的 argparse 解析器。"""
        parser = ArgumentParser(
            description=_("subtitler —— 字幕格式互转工具。"),
            add_help=False,
        )
        parser.add_argument(
            "input",
            nargs="?",
            type=Path,
            metavar="INPUT",
            help=_("输入字幕文件，格式按扩展名识别"),
        )
        parser.add_argument(
            "output",
            nargs="?",
            type=Path,
            metavar="OUTPUT",
            help=_("输出字幕文件，格式按扩展名识别"),
        )
        parser.add_argument(
            "-d",
            "--debug",
            dest="debug_mode",
            action="store_true",
            help=_("开启 debug 模式"),
        )
        parser.add_argument(
            "-h",
            "--help",
            dest="show_help",
            action="store_true",
            default=False,
            help=_("显示分组帮助"),
        )
        parser.add_argument(
            "--tutorial",
            dest="show_full_help",
            action="store_true",
            default=False,
            help=_("显示完整教程"),
        )
        return parser
