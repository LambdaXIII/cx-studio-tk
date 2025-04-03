from argparse import ArgumentParser
from dataclasses import asdict

from cx_studio.core import DataPackage
from pathlib import Path
from .prober import Prober
from rich.console import Console


class Application:
    APP_NAME = "FootageHunter"
    APP_VERSION = "0.1.0"
    @staticmethod
    def get_appcontext() -> DataPackage:
        parser = ArgumentParser(prog=Application.APP_NAME)
        parser.add_argument("inputs", nargs="*", help="Input files")
        parser.add_argument("-f", "--force", help="Extract any path from input files.",
                            action="store_true",dest="force_mode")
        parser.add_argument("-e","--existed-only",help="Check if file exists",
                            action="store_true",dest="existed_only")
        parser.add_argument("-i","--include",help="include search paths for relative paths",
                            action="store",nargs="*",dest="search_paths")
        parser.add_argument("-o","--output",help="Save file list to some file.",
                            action="store")
        parser.add_argument("-v","--version",
                            action="version",version=f"{Application.APP_NAME} {Application.APP_VERSION}")
        parser.add_argument("--full-help","--tutorial",help="Show tutorial",
                            action="store_true",dest="show_full_help")

        args = parser.parse_args()
        return DataPackage(**vars(args))

    def __init__(self):
        self.context = DataPackage()
        self.console = Console()
        self.err_console = Console(stderr=True)

    def print(self,*args,**kwargs):
        self.console.print(*args,**kwargs)

    def say(self, *args, **kwargs):
        self.err_console.print(*args,**kwargs)

    def __enter__(self):
        self.context.update(Application.get_appcontext())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.say("[grey]Bye ~[/grey]")
        return False

    def iter_results(self):
        exported = set()
        for s in self.context.inputs:
            source = Path(s)
            if not source.exists():
                self.say(f"[red]File not found:[/red] [yellow]{source}[/yellow]")
                continue
            with Prober(source,
                        force_mode=self.context.force_mode,
                        existed_only=self.context.existed_only,
                        include_folders=self.context.search_paths
                        ) as prober:
                for p in prober.probe():
                    if p in exported:
                        continue
                    exported.add(p)
                    yield p



    def run(self):
        if self.context.show_full_help:
            print("TODO: Show full help")
            return

        result = []
        for i in self.iter_results():
            self.print(str(i))
            result.append(str(i))

        if self.context.output:
            self.say("[green]Saved to:[/green] [yellow]{}[/yellow]".format(self.context.output))
            with open(self.context.output,"w") as f:
                f.write("\n".join(result))



