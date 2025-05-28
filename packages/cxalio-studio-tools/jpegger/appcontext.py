from argparse import ArgumentParser
from collections.abc import Sequence


class AppContext:
    def __init__(self, **kwargs):
        self.inputs: list[str] = []

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

        return parser
