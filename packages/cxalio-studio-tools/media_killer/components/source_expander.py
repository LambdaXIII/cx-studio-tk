from .preset import Preset
from cx_studio.path_expander import PathExpander, SuffixValidator
from cx_tools_common.path_prober import *
from cx_studio.utils import EncodingUtils
from collections.abc import Generator


class SourceExpander:
    def __init__(self, preset:Preset):
        self.preset = preset
        self._source_probers = [
            FcpXMLProber(),
            Fcp7XMLProber(),
            # OTIOProber(),
            ResolveMetadataCSVProber(),
            EDLProber(),
            TextProber(".txt")
        ]

    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def _pre_expand(self,*paths):
        for path in paths:
            path = Path(path)
            probed = False
            if path.exists():
                for prober in self._source_probers:
                    pre_check = prober.pre_check(path)
                    if not pre_check:
                        continue
                    encoding = EncodingUtils.detect_encoding(path)
                    with open(path, 'r',encoding=encoding) as fp:
                        if prober.is_acceptable(fp):
                            yield from prober.probe(fp)
                            probed = True
                            break
            if not probed:
                yield path

    def expand(self,*paths) -> Generator[Path]:
        expander_start_info = PathExpander.StartInfo(
            accept_dirs=False,
            file_validator=SuffixValidator(self.preset.source_suffixes),
        )

        expander = PathExpander(expander_start_info)
        for source in self._pre_expand(*paths):
            yield from expander.expand(source)




