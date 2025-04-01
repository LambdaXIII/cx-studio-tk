from argparse import ArgumentParser


from .appcontext import AppContext
from collections import Sequence
from pathlib import Path
from cx_studio.utils import PathUtils


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
            pp = Path(PathUtils.force_suffix(p, ".toml"))
            return pp.exists()
        return p.suffix == ".toml"

    @staticmethod
    def make_context(arguments: Sequence[str] | None = None) -> AppContext:
        result = AppContext()

        parser = self.make_parser()
        args = parser.parse_args(arguments)

        result.tutorial = args.tutorial
        result.generate = args.generate

        for source in args.sources:
            if self._is_preset(source):
                result.presets.append(source)
            else:
                result.sources.append(source)

        result.script_output = args.save_script
        result.pretending_mode = args.pretend
        result.debug = args.debug
        result.sort_mode = args.sort
        result.continue_mode = args.continue_mode
        return result
