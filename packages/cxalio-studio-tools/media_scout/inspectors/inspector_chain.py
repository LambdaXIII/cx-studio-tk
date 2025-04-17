import os
from pathlib import PurePath, Path
from typing import Self
from collections.abc import Iterable
from media_scout.inspectors.media_path_inspector import MediaPathInspector
from .edl_inspector import EDLInspector
from .fcpxml_inspector import FCPXMLInspector, FCPXMLDInspector
from .inspector_info import InspectorInfo
from .legacy_xml_inspector import LegacyXMLInspector
from .resolve_metadata_inspector import ResolveMetadataInspector


class InspectorChain:
    def __init__(
        self,
        *inspectors: MediaPathInspector,
        allow_duplicated: bool = False,
        auto_resolve: bool = False,
    ):
        self.allow_duplicated = allow_duplicated
        self.auto_resolve = auto_resolve
        self._inspectors: list[MediaPathInspector] = []
        self._inspectors.extend(inspectors)
        self._exported_paths: set[PurePath] = set()

    def add_inspector(self, inspector: MediaPathInspector) -> Self:
        self._inspectors.append(inspector)
        return self

    def _auto_resolve(self, path: os.PathLike, info: InspectorInfo) -> PurePath:
        x = Path(path)
        if not self.auto_resolve:
            return x
        if not x.is_absolute():
            x = Path(info.path.parent, x)
        return x.resolve() if x.exists() else x

    def inspect(self, info: InspectorInfo) -> Iterable[PurePath]:
        for inspector in self._inspectors:
            if inspector.is_inspectable(info):
                for path in inspector.inspect(info):
                    path = self._auto_resolve(path, info)
                    if self.allow_duplicated or path not in self._exported_paths:
                        self._exported_paths.add(path)
                        yield path
                break

    def __enter__(self) -> Self:
        self._exported_paths.clear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exported_paths.clear()
        return False
