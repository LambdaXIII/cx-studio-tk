from argparse import ArgumentParser
from collections.abc import Sequence
from email.mime import image
from pydoc import describe
from cx_studio.utils import TextUtils
from cx_wealth import WealthHelp
from cx_wealth import rich_types as r


class SimpleAppContext:
    def __init__(self, **kwargs):
        self.inputs: list[str] = []
        self.show_help: bool = False
        self.scale_factor: float | None = None
        self.size: str | None = None
        self.width: int | None = None
        self.height: int | None = None
        self.color_space: str | None = None
        self.format: str | None = None
        self.quality: int | None = None
        self.output_dir: str | None = None
        self.overwrite: bool = False
        self.debug_mode: bool = False

        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    def __rich_repr__(self):
        yield from self.__dict__.items()

    @classmethod
    def from_arguments(cls, arguments: Sequence[str] | None = None):
        parser = cls.__make_parser()
        args = parser.parse_args(arguments)
        return cls(**vars(args))

    @staticmethod
    def __make_parser() -> ArgumentParser:
        parser = ArgumentParser(
            description="Jpegger 是一个简单的批量转换图片的命令行工具。", add_help=False
        )

        parser.add_argument("inputs", nargs="*")
        parser.add_argument(
            "--help", "-h", action="store_true", help="显示帮助信息", dest="show_help"
        )
        parser.add_argument("--scale", action="store", dest="scale_factor")
        parser.add_argument("--size", "-s", action="store", dest="size")
        parser.add_argument("--width", action="store", dest="width")
        parser.add_argument("--height", action="store", dest="height")
        parser.add_argument(
            "--color-space", "-c", choices=["RGB", "CMYK", "L"], dest="color_space"
        )
        parser.add_argument("--format", "-f", action="store", dest="format")
        parser.add_argument("--quality", "-q", action="store", dest="quality")
        parser.add_argument("--output", "-o", action="store", dest="output_dir")
        parser.add_argument(
            "--force-overwrite", "-y", action="store_true", dest="overwrite"
        )
        parser.add_argument("--debug", "-d", action="store_true", dest="debug_mode")

        return parser

    def __rich_detail__(self):
        ignore_text = "[red](忽略)[/red]"
        if self.scale_factor:
            yield "缩放因子", self.scale_factor
        if self.size:
            yield f"缩放尺寸{ignore_text if self.scale_factor else ""}", self.size
        if self.width:
            yield f"缩放宽度{ignore_text if self.scale_factor or self.size else ""}", self.width
        if self.height:
            yield f"缩放高度{ignore_text if self.scale_factor or self.size else ""}", self.height
        if self.color_space:
            yield "颜色空间", self.color_space
        if self.quality:
            yield "编码质量", self.quality
        if self.output_dir:
            yield "输出目录", self.output_dir
        if self.overwrite:
            yield "强制覆盖", self.overwrite
        if self.debug_mode:
            yield "调试模式", self.debug_mode

        known_keys = [
            "inputs",
            "show_help",
            "scale_factor",
            "size",
            "width",
            "height",
            "color_space",
            "format",
            "quality",
            "output_dir",
            "overwrite",
            "debug_mode",
        ]
        other_values = {k: v for k, v in self.__dict__.items() if k not in known_keys}

        yield from other_values.items()

        if self.inputs:
            yield "输入文件", self.inputs


class SimpleHelp(WealthHelp):
    def __init__(self):
        super().__init__(prog="jpegger")
        self.description = TextUtils.unwrap(
            """Jpegger是一个简单的批量转换图片的命令行工具。

            使用选项可以简单地控制输出图片的尺寸、编码质量和色彩空间。
            本工具旨在快速地进行简单的批量处理，所以暂不提供更高级的客制化功能。
            """
        )
        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

        basic_opts = self.add_group("基本选项")
        basic_opts.add_action(
            "inputs", nargs="+", metavar="FILE", description="需要转码的文件"
        )
        basic_opts.add_action(
            "-f",
            "--format",
            metavar="FORMAT",
            description="指定输出格式，默认沿用原始格式",
        )
        basic_opts.add_action(
            "-q",
            "--quality",
            metavar="QUALITY",
            description="指定输出质量，默认使用内置的常用质量设置",
        )
        basic_opts.add_action(
            "-o", "--output", metavar="DIR", description="输出目录，默认为当前目录"
        )

        image_controls = self.add_group("图片处理", "对图像进行处理")
        image_controls.add_action(
            "--scale", metavar="FACTOR", description="按比例缩放图片的尺寸"
        )
        image_controls.add_action(
            "-s",
            "--size",
            metavar="WIDTHxHEIGHT",
            description="指定图片的尺寸，接受包含两个数字的表达式",
        )
        image_controls.add_action(
            "--width",
            metavar="WIDTH",
            description="指定图片的宽度，如果未指定高度则保持原始图像比例",
        )
        image_controls.add_action(
            "--height",
            metavar="HEIGHT",
            description="指定图片的高度，如果未指定宽度则保持原始图像比例",
        )

        process_control = self.add_group("其它选项")
        process_control.add_action(
            "--overwrite",
            "-y",
            description="强制覆盖已存在的文件，未设置时将会自动重命名目标文件",
        )
        process_control.add_action("--debug", description="显示调试信息")
        process_control.add_action("-h", "--help", description="显示帮助信息")
