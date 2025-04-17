from argparse import ArgumentParser
from dataclasses import dataclass
from collections.abc import Sequence
from xml.etree.ElementInclude import include

from cx_studio.utils.cx_textutils import auto_quote


class ArgParser(ArgumentParser):
    def __init__(self):
        super().__init__(
            prog="MediaScout",
            description="MediaScout is a tool for inspecting media files.",
            epilog="",
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
            "-q", "--auto-quote", action="store_true", default=False, dest="auto_quote"
        )
        self.add_argument(
            "--auto-resolve", action="store_true", default=False, dest="auto_resolve"
        )
        self.add_argument(
            "-d", "--debug", action="store_true", default=False, dest="debug_mode"
        )


@dataclass
class AppContext:
    inputs: list[str]
    includes: list[str]
    output: str | None
    allow_duplicated: bool
    auto_resolve: bool
    existed_only: bool
    auto_quote: bool
    debug_mode: bool

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
            auto_quote=args.auto_quote,
            debug_mode=args.debug_mode,
        )

    def __rich_detail__(self):
        yield from self.__dict__.items()
