from argparse import ArgumentParser
from collections.abc import Sequence


class AppContext:
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

    def __rich_detail__(self):
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
        parser.add_argument("--format", "-f", choices=["jpg", "png"], dest="format")
        parser.add_argument("--quality", "-q", action="store", dest="quality")
        parser.add_argument("--output", "-o", action="store", dest="output_dir")
        parser.add_argument(
            "--force-overwrite", "-y", action="store_true", dest="overwrite"
        )
        parser.add_argument("--debug", "-d", action="store_true", dest="debug_mode")

        return parser
