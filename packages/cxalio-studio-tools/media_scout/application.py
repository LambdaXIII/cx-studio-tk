import os
from pathlib import Path, PurePath
import time
from cx_tools.app import IApplication

from collections.abc import Iterable
from .appenv import appenv
from media_scout.inspectors.filelist_inspector import FileListInspector
from cx_studio.filesystem import auto_suffix, quote_path

from cx_wealth import WealthDetailPanel
from rich.rule import Rule

from .inspectors import (
    ResolveMetadataInspector,
    MediaPathInspector,
    InspectorInfo,
    EDLInspector,
    LegacyXMLInspector,
    FCPXMLInspector,
    FCPXMLDInspector,
    InspectorChain,
)
from .arg_parser import MSHelp


class Application(IApplication):
    APP_NAME = "MediaScout"
    APP_VERSION = "0.1.0"

    def __init__(self):
        super().__init__()

    def start(self):
        appenv.start()
        appenv.show_banner()
        appenv.whisper("MediaScout 启动")
        appenv.whisper(WealthDetailPanel(appenv.context))

    def stop(self):
        appenv.stop()
        appenv.whisper("Bye~")

    @staticmethod
    def resolve(path: os.PathLike) -> str | None:
        result = Path(path)
        if appenv.context.existed_only and not result.exists():
            appenv.whisper("[red]{} 不存在[/]".format(result))
            return None
        if appenv.context.auto_resolve:
            result = result.resolve()
        return quote_path(result, appenv.context.quote_mode)

    @staticmethod
    def auto_expand(path: os.PathLike, info: InspectorInfo) -> Iterable[PurePath]:
        result = Path(path)
        includes = [info.path.parent.resolve()] if appenv.context.auto_resolve else []
        includes.extend([Path(x) for x in appenv.context.includes])

        if result.is_absolute() or not appenv.context.includes:
            yield result
        else:
            appenv.whisper("[red]在搜索路径中搜索：{}[/]".format(result))
            for include in includes:
                p = Path(include).absolute() / result
                if p.exists():
                    appenv.whisper("找到：{}".format(p))
                    yield p

    def iter_results(self):
        inspectors = [
            ResolveMetadataInspector(),
            EDLInspector(),
            LegacyXMLInspector(),
            FCPXMLInspector(),
            FCPXMLDInspector(),
            FileListInspector(".txt", ".ps1", ".sh"),
        ]

        chain = InspectorChain(
            *inspectors, allow_duplicated=appenv.context.allow_duplicated
        )

        for path in appenv.context.inputs:
            path = Path(path)
            appenv.say(Rule(path.name, style="dim green"))
            info = InspectorInfo(Path(path))
            for result in chain.inspect(info):
                for x in self.auto_expand(result, info):
                    if a := self.resolve(x):
                        yield a

    def run(self):
        if appenv.context.show_help:
            MSHelp.show_help(appenv.console)
            return

        if appenv.context.show_full_help:
            MSHelp.show_full_help(appenv.console)
            return

        if appenv.context.allow_duplicated:
            appenv.say("[red]允许输出重复项[/]")
            time.sleep(0.5)
        if appenv.context.auto_resolve:
            appenv.say("[yellow]自动整理或折叠路径[/]")
            time.sleep(0.5)
        if appenv.context.existed_only:
            appenv.say("[green]只输出存在的文件[/]")
            time.sleep(0.5)

        result = []
        for x in self.iter_results():
            result.append(x)
            appenv.print(x)

        appenv.say("[yellow]共找到 {} 个媒体路径。[/]".format(len(result)))

        if appenv.context.output:
            output_file = auto_suffix(appenv.context.output, ".txt")
            with open(output_file, "w") as fp:
                for x in result:
                    fp.write(str(x) + "\n")

            appenv.say('[green]列表已保存到："{}"[/]'.format(output_file))
