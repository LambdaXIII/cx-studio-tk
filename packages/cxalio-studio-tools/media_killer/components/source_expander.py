from collections.abc import Generator

from cx_studio.path_expander import PathExpander, SuffixValidator
from cx_studio.utils import EncodingUtils
from cx_tools_common.path_prober import *
from media_killer.appenv import appenv
from .preset import Preset


class SourceExpander:
    def __init__(self, preset: Preset):
        self.preset = preset
        self._source_probers = [
            FcpXMLProber(),
            Fcp7XMLProber(),
            # OTIOProber(),
            ResolveMetadataCSVProber(),
            EDLProber(),
            TextProber(".txt"),
        ]

    def _pre_expand(self, *paths):
        for path in paths:
            path = Path(path)
            probed = False
            if path.exists():
                for prober in self._source_probers:
                    pre_check = prober.pre_check(path)
                    if not pre_check:
                        continue
                    encoding = EncodingUtils.detect_encoding(path)
                    with open(path, "r", encoding=encoding) as fp:
                        if prober.is_acceptable(fp):
                            yield from prober.probe(fp)
                            probed = True
                            break
            if not probed:
                yield path

    def expand(self, *paths) -> Generator[Path]:
        expander_start_info = PathExpander.StartInfo(
            accept_dirs=False,
            file_validator=SuffixValidator(self.preset.source_suffixes),
        )

        expander = PathExpander(expander_start_info)
        for source in self._pre_expand(*paths):
            if appenv.wanna_quit:
                appenv.whisper("接收到[bold]取消信号[/bold]，中断路径展开操作。")
                break
            yield from expander.expand(source)
