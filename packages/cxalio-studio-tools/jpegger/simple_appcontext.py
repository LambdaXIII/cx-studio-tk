"""Jpegger 简单应用上下文与帮助系统。

`SimpleAppContext` 是命令行参数解析后的值对象，采用 `from_arguments()`
工厂方法构造，并通过 kwargs 白名单完成字段赋值。`SimpleHelp` 使用
`WealthHelp` DSL 提供与 argparse 一致的中文帮助文本。
"""

from collections.abc import Generator, Sequence
from argparse import ArgumentParser
from typing import Any

from cx_studio import text as tt
from cx_tools.i18n import _
from cx_wealth import WealthHelp


class SimpleAppContext:
    """Jpegger 命令行上下文。

    字段通过 `from_arguments()` 解析并赋值。未在 `__init__` 中声明的
    kwargs 会被静默忽略，形成白名单效果。

    Attributes:
        inputs: 输入文件列表。
        show_help: 是否显示帮助。
        scale_factor: 比例缩放因子。
        size: 形如 "WIDTHxHEIGHT" 的目标尺寸字符串。
        width: 目标宽度（像素）。
        height: 目标高度（像素）。
        color_space: 目标色彩空间。
        target_format: 目标格式名称（CLI 选项名为 `--format`）。
        quality: 编码质量。
        output_dir: 输出目录。
        overwrite: 是否强制覆盖。
        debug_mode: 是否开启调试输出。
    """

    def __init__(self, **kwargs: Any):
        """用 kwargs 白名单初始化上下文字段。"""
        self.inputs: list[str] = []
        self.show_help: bool = False
        self.scale_factor: float | None = None
        self.size: str | None = None
        self.width: int | None = None
        self.height: int | None = None
        self.color_space: str | None = None
        self.target_format: str | None = None
        self.quality: int | None = None
        self.output_dir: str | None = None
        self.overwrite: bool = False
        self.debug_mode: bool = False

        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    def __rich_repr__(self) -> Generator[tuple[str, Any], None, None]:
        """返回所有字段的 `(name, value)` 表示，用于 debug 详情面板。"""
        yield from self.__dict__.items()

    @classmethod
    def from_arguments(
        cls, arguments: Sequence[str] | None = None
    ) -> "SimpleAppContext":
        """从命令行参数构造上下文。

        Args:
            arguments: 要解析的字符串序列；None 时使用 `sys.argv[1:]`。

        Returns:
            解析后的 `SimpleAppContext` 实例。
        """
        parser = cls.__make_parser()
        args = parser.parse_args(arguments)
        return cls(**vars(args))

    @staticmethod
    def __make_parser() -> ArgumentParser:
        """构建 Jpegger 的 argparse 解析器。"""
        parser = ArgumentParser(
            description=_("Jpegger 是一个简单的批量转换图片的命令行工具。"),
            add_help=False,
        )

        parser.add_argument("inputs", nargs="*")
        parser.add_argument(
            "--help",
            "-h",
            action="store_true",
            help=_("显示帮助信息"),
            dest="show_help",
        )
        parser.add_argument("--scale", action="store", dest="scale_factor", type=float)
        parser.add_argument("--size", "-s", action="store", dest="size")
        parser.add_argument("--width", action="store", dest="width", type=int)
        parser.add_argument("--height", action="store", dest="height", type=int)
        parser.add_argument(
            "--color-space", "-c", choices=["RGB", "L", "CMYK"], dest="color_space"
        )
        parser.add_argument("--format", "-f", action="store", dest="target_format")
        parser.add_argument("--quality", "-q", action="store", dest="quality", type=int)
        parser.add_argument("--output", "-o", action="store", dest="output_dir")
        parser.add_argument(
            "--force-overwrite", "-y", action="store_true", dest="overwrite"
        )
        parser.add_argument("--debug", "-d", action="store_true", dest="debug_mode")

        return parser

    def __rich_detail__(self) -> Generator[tuple[str, Any], None, None]:
        """为详情面板列出生效的上下文参数。

        当 scale/size/width/height 存在互斥或覆盖关系时，用红色
        "(忽略)" 提示用户实际生效的参数。
        """
        ignore_text = "[red](忽略)[/red]"
        if self.scale_factor:
            yield _("缩放因子"), self.scale_factor
        if self.size:
            yield _("缩放尺寸") + (ignore_text if self.scale_factor else ""), self.size
        if self.width:
            yield _("缩放宽度") + (
                ignore_text if self.scale_factor or self.size else ""
            ), self.width
        if self.height:
            yield _("缩放高度") + (
                ignore_text if self.scale_factor or self.size or self.width else ""
            ), self.height
        if self.color_space:
            yield _("颜色空间"), self.color_space
        if self.quality:
            yield _("编码质量"), self.quality
        if self.output_dir:
            yield _("输出目录"), self.output_dir
        if self.overwrite:
            yield _("强制覆盖"), self.overwrite
        if self.debug_mode:
            yield _("调试模式"), self.debug_mode

        known_keys = [
            "inputs",
            "show_help",
            "scale_factor",
            "size",
            "width",
            "height",
            "color_space",
            "target_format",
            "quality",
            "output_dir",
            "overwrite",
            "debug_mode",
        ]
        other_values = {k: v for k, v in self.__dict__.items() if k not in known_keys}

        yield from other_values.items()

        if self.inputs:
            yield _("输入文件"), self.inputs


class SimpleHelp(WealthHelp):
    """Jpegger 的中文帮助文档。"""

    description: str
    epilog: str

    def __init__(self):
        """使用 WealthHelp DSL 构建帮助内容。"""
        super().__init__(prog="jpegger")
        self.description = tt.auto_unwrap(
            _("""Jpegger是一个简单的批量转换图片的命令行工具。

            使用选项可以简单地控制输出图片的尺寸、编码质量和色彩空间。
            本工具旨在快速地进行简单的批量处理，所以暂不提供更高级的客制化功能。
            """)
        )
        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

        basic_opts = self.add_group(_("基本选项"))
        _action = basic_opts.add_action(
            "inputs", nargs="+", metavar="FILE", description=_("需要转码的文件")
        )
        _action = basic_opts.add_action(
            "-f",
            "--format",
            metavar="FORMAT",
            description=_("指定输出格式，默认沿用原始格式"),
        )
        _action = basic_opts.add_action(
            "-q",
            "--quality",
            metavar="QUALITY",
            description=_("指定输出质量，默认使用内置的常用质量设置"),
        )
        _action = basic_opts.add_action(
            "-o", "--output", metavar="DIR", description=_("输出目录，默认为当前目录")
        )

        image_controls = self.add_group(_("图片处理"), _("对图像进行处理"))
        _action = image_controls.add_action(
            "--scale", metavar="FACTOR", description=_("按比例缩放图片的尺寸")
        )
        _action = image_controls.add_action(
            "-s",
            "--size",
            metavar="WIDTHxHEIGHT",
            description=_("指定图片的尺寸，接受包含两个数字的表达式"),
        )
        _action = image_controls.add_action(
            "--width",
            metavar="WIDTH",
            description=_("指定图片的宽度，如果未指定高度则保持原始图像比例"),
        )
        _action = image_controls.add_action(
            "--height",
            metavar="HEIGHT",
            description=_("指定图片的高度，如果未指定宽度则保持原始图像比例"),
        )

        process_control = self.add_group(_("其它选项"))
        _action = process_control.add_action(
            "--force-overwrite",
            "-y",
            description=_("强制覆盖已存在的文件，未设置时将会自动重命名目标文件"),
        )
        _action = process_control.add_action("--debug", description=_("显示调试信息"))
        _action = process_control.add_action(
            "-h", "--help", description=_("显示帮助信息")
        )
