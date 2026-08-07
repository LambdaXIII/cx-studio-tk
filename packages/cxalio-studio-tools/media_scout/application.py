import os
import time
from collections.abc import Iterable
from pathlib import Path, PurePath
from typing import override

from cx_studio.filesystem import PathUtils
from cx_tools.app import IApplication, IAppContext, IAppEnvironment
from cx_wealthy import WealthyDetailPanel, rich_types as r
from media_scout.common.inspectors.filelist_inspector import FileListInspector
from media_scout.i18n import _
from .app_help import MediaScoutHelp
from .appcontext import MediaScoutContext
from .common.inspectors import (
    ResolveMetadataInspector,
    InspectorInfo,
    EDLInspector,
    LegacyXMLInspector,
    FCPXMLInspector,
    FCPXMLDInspector,
    InspectorChain,
)


class MediaScoutApp(IApplication):
    """MediaScout 应用。

    编排 appenv + context，驱动媒体文件检查流程。
    """

    def __init__(
        self,
        appenv: IAppEnvironment,
        context: MediaScoutContext,
    ) -> None:
        super().__init__(appenv, context)
        self.context = context
        self._data_console = r.Console()

    def start(self):
        self.appenv.set_debug_mode(self.context.debug_mode)
        self.appenv.say(
            f"[cx.info]{self.appenv.app_name}[/] [cx.number]v{self.appenv.app_version}[/]"
        )
        self.appenv.whisper(_("MediaScout 启动"))
        self.appenv.whisper(WealthyDetailPanel(self.context))

    def stop(self):
        self.appenv.whisper("Bye~")

    @override
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is KeyboardInterrupt:
            self.appenv.say(f"[cx.warning]{_('用户中断')}[/]")
            result = True
        return result

    def resolve(self, path: os.PathLike) -> str | None:
        """解析并引用路径。

        根据 context 的 existed_only、auto_resolve、quote_mode 选项处理路径。
        """
        result = Path(path)
        if self.context.existed_only and not result.exists():
            self.appenv.whisper(f"[cx.error]{result} {_('不存在')}[/]")
            return None
        if self.context.auto_resolve:
            result = result.resolve()
        return PathUtils.quote_path(result, self.context.quote_mode)

    def auto_expand(self, path: os.PathLike, info: InspectorInfo) -> Iterable[PurePath]:
        """在搜索路径中自动展开相对路径。"""
        result = Path(path)
        includes = [info.path.parent.resolve()] if self.context.auto_resolve else []
        includes.extend([Path(x) for x in self.context.includes])

        if result.is_absolute() or not self.context.includes:
            yield result
        else:
            self.appenv.whisper(f"[cx.warning]{_('在搜索路径中搜索：')}{result}[/]")
            for include in includes:
                p = Path(include).absolute() / result
                if p.exists():
                    self.appenv.whisper(f"{_('找到：')}{p}")
                    yield p

    def iter_results(self):
        """遍历所有输入文件的检查结果。"""
        inspectors = [
            ResolveMetadataInspector(),
            EDLInspector(),
            LegacyXMLInspector(),
            FCPXMLInspector(),
            FCPXMLDInspector(),
            FileListInspector(".txt", ".ps1", ".sh"),
        ]

        chain = InspectorChain(
            *inspectors, allow_duplicated=self.context.allow_duplicated
        )

        for path in self.context.inputs:
            path = Path(path)
            self.appenv.say(r.Rule(path.name, style="dim green"))
            info = InspectorInfo(Path(path))
            for result in chain.inspect(info):
                for x in self.auto_expand(result, info):
                    if a := self.resolve(x):
                        yield a

    def run(self):
        """执行 MediaScout 主逻辑。"""
        if self.context.show_help:
            help_component = MediaScoutHelp(self.appenv, self.context)
            help_component.show_help()
            return

        if self.context.show_full_help:
            help_component = MediaScoutHelp(self.appenv, self.context)
            help_component.show_full_help()
            return

        if self.context.allow_duplicated:
            self.appenv.say(f"[cx.warning]{_('允许输出重复项')}[/]")
            time.sleep(0.5)
        if self.context.auto_resolve:
            self.appenv.say(f"[cx.warning]{_('自动整理或折叠路径')}[/]")
            time.sleep(0.5)
        if self.context.existed_only:
            self.appenv.say(f"[cx.info]{_('只输出存在的文件')}[/]")
            time.sleep(0.5)

        result = []
        for x in self.iter_results():
            result.append(x)
            self._data_console.print(x)

        self.appenv.say(
            f"[cx.info]{_('共找到 {count} 个媒体路径。').format(count=len(result))}[/]"
        )

        if self.context.output:
            output_file = PathUtils.auto_suffix(self.context.output, ".txt")
            with open(output_file, "w") as fp:
                for x in result:
                    fp.write(str(x) + "\n")

            self.appenv.say(
                f"[cx.success]{_('列表已保存到：{path}').format(path=output_file)}[/]"
            )
