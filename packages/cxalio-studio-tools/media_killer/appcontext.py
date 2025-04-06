from argparse import ArgumentParser
from collections.abc import Sequence


class AppContext:
    def __init__(self, **kwargs):
        self.inputs: list[str] = []
        self.script_output: str | None = None
        self.pretending_mode: bool = False
        self.debug_mode: bool = False
        self.sort_mode: str = "x"
        self.continue_mode: bool = False
        self.generate: bool = False
        self.save_script: str | None = None
        self.show_full_help: bool = False
        self.force_overwrite: bool = False
        self.force_no_overwrite: bool = False

        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    def __rich_repr__(self):
        yield from self.__dict__.items()

    @staticmethod
    def __make_parser() -> ArgumentParser:
        parser = ArgumentParser()
        parser.add_argument(
            "--tutorial",
            "--full-help",
            action="store_true",
            help="Show full tutorial.",
            dest="show_full_help",
        )
        parser.add_argument(
            "-g",
            "--generate",
            help="Generate script file.",
            action="store_true",
            default=False,
            dest="generate",
        )
        parser.add_argument("--save-script", "-s", help="Generate script file")
        parser.add_argument(
            "--sort",
            help="Set sorting mode",
            choices=["source", "components", "target", "x"],
            default="x",
            dest="sort_mode",
        )
        parser.add_argument(
            "--overwrite",
            "-y",
            help="Force overwrite outputs",
            action="store_true",
            default=False,
            dest="force_overwrite",
        )

        parser.add_argument(
            "--no-overwrite",
            "-n",
            help="Force no overwrite on outputs",
            action="store_true",
            default=False,
            dest="force_no_overwrite",
        )

        parser.add_argument(
            "-c",
            "--continue",
            action="store_true",
            help="Continue last task.",
            dest="continue_mode",
        )
        parser.add_argument(
            "-p",
            "--pretend",
            help="Pretend to execute task.",
            action="store_true",
            dest="pretending_mode",
        )
        parser.add_argument(
            "-d",
            "--debug",
            help="Start debug mode.",
            action="store_true",
            dest="debug_mode",
        )
        parser.add_argument("inputs", help="Sources to process", nargs="*")
        return parser

    @classmethod
    def from_arguments(cls, arguments: Sequence[str] | None = None):
        parser = cls.__make_parser()
        args = parser.parse_args(arguments)
        return cls(**vars(args))
