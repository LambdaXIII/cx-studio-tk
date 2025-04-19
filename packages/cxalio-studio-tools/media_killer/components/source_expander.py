from collections.abc import Generator, Iterable
from pathlib import Path, PurePath

from cx_studio.path_expander import PathExpander, SuffixValidator
from media_killer.appenv import appenv
from media_scout.inspectors import (
    EDLInspector,
    FCPXMLDInspector,
    FCPXMLInspector,
    FileListInspector,
    InspectorChain,
    ResolveMetadataInspector,
)
from media_scout.inspectors.inspector_info import InspectorInfo
from .preset import Preset


class SourceExpander:
    def __init__(self, preset: Preset):
        self.preset = preset
        self._exported_paths = set()
        self._source_inspector = InspectorChain(
            EDLInspector(),
            FCPXMLDInspector(),
            FCPXMLInspector(),
            ResolveMetadataInspector(),
            FileListInspector(".txt", ".csv"),
            auto_resolve=True,
        )

    def _pre_expand(self, *paths) -> Iterable[PurePath]:
        for path in paths:
            path = Path(path)
            info = InspectorInfo(path)
            inspected = list(self._source_inspector.inspect(info))
            if inspected:
                yield from inspected
            else:
                yield path

    def expand(self, *paths) -> Generator[Path]:
        expander_start_info = PathExpander.StartInfo(
            accept_dirs=False,
            file_validator=SuffixValidator(self.preset.source_suffixes),
        )

        expander = PathExpander(expander_start_info)
        for source in self._pre_expand(*paths):
            wanna_quit = False
            if appenv.wanna_quit_event.is_set():
                wanna_quit = True
                appenv.wanna_quit_event.clear()
            if wanna_quit:
                appenv.whisper("接收到[bold]取消信号[/bold]，中断路径展开操作。")
                break
            for p in expander.expand(Path(source)):
                if p in self._exported_paths:
                    continue
                self._exported_paths.add(p)
                yield p
