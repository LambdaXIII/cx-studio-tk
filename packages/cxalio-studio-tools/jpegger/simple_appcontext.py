from argparse import ArgumentParser
from collections.abc import Sequence


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
