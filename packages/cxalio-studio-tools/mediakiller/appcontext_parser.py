from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path

from cx_studio.utils import path_utils
from .appcontext import AppContext


class AppContextParser:

    @staticmethod
    def make_parser() -> ArgumentParser:
        parser = ArgumentParser()
        parser.add_argument(
            "--tutorial", action="store_true", help="Show full tutorial."
        )
        parser.add_argument(
            "-g", "--generate", help="Generate script file.", default=None
        )
        parser.add_argument("--save-script", "-s", help="Generate script file")
        parser.add_argument(
            "--sort",
            choices=["source", "components", "target", "x"],
            default="x",
            help="Set sorting mode",
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
            "-p", "--pretend", action="store_true", help="Pretend to execute task."
        )
        parser.add_argument(
            "-d", "--debug", action="store_true", help="Start debug mode."
        )
        parser.add_argument("sources", nargs="*", help="Sources to process")
        return parser

    @staticmethod
    def _is_preset(p: Path) -> bool:
        p = Path(p)
        if p.suffix == "":
            pp = Path(path_utils.force_suffix(p, ".toml"))
            return pp.exists()
        return p.suffix == ".toml"

    @staticmethod
    def make_context(arguments: Sequence[str] | None = None) -> AppContext:
        result = AppContext()

        parser = AppContextParser.make_parser()
        args = parser.parse_args(arguments)

        result.tutorial = args.tutorial
        result.generate = args.generate

        for source in args.sources:
            if AppContextParser._is_preset(source):
                result.presets.append(source)
            else:
                result.sources.append(source)

        result.script_output = args.save_script
        result.pretending_mode = args.pretend
        result.debug = args.debug
        result.sort_mode = args.sort
        result.continue_mode = args.continue_mode
        result.force_overwrite = args.force_overwrite
        result.force_no_overwrite = args.force_no_overwrite
        return result
