from cx_studio.utils import EncodingUtils
from cx_tools_common.path_prober import *
from collections.abc import Collection

class Prober:
    def __init__(self, filename: Path, force_mode: bool = False,
                 existed_only: bool = False,
                 include_folders: Collection[str | Path] | None = None):
        self._filename = filename
        self._fp = None

        self._existed_only = existed_only
        self._include_folders = {Path(filename).resolve().parent}
        self._include_folders.union(include_folders) if include_folders else None

        self._probers: list[IPathProber] = [
            FcpXMLProber(),
            Fcp7XMLProber(),
            # OTIOProber(),
            ResolveMetadataCSVProber(),
            EDLProber(),
        ]
        if force_mode:
            self._probers.append(TextProber())
        else:
            self._probers.append(TextProber(".txt", ".list"))

    def __enter__(self):
        encoding = EncodingUtils.detect_encoding(self._filename)
        self._fp = open(self._filename, "r", encoding=encoding)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fp.close()
        self._fp = None
        return False

    def _check_relative_paths(self, p: Path):
        if p.is_absolute():
            yield p
        else:
            for folder in self._include_folders:
                if folder.is_absolute():
                    yield folder.joinpath(p).resolve()
                else:
                    yield Path.cwd().joinpath(folder).joinpath(p).resolve()

    def probe(self):
        for prober in self._probers:
            if prober.is_acceptable(self._fp):
                for p in prober.probe(self._fp):
                    path = Path(p)
                    for px in self._check_relative_paths(path):
                        if self._existed_only and not px.exists():
                            continue
                        yield px
                break
