from pathlib import Path
from cx_tools_common.app_interface import IApplication
import sys

from media_scout.inspectors.filelist_inspector import FileListInspector

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


class Application(IApplication):
    APP_NAME = "MediaScout"
    APP_VERSION = "0.1.0"

    def __init__(self):
        super().__init__()

    def start(self):
        print("Starting MediaScout")

    def stop(self):
        print("Stopping MediaScout")

    @staticmethod
    def probe(filename: Path):
        inspector = FCPXMLDInspector()
        sample = InspectorInfo(filename)
        if inspector.is_inspectable(sample):
            print("OK")
            for x in inspector.inspect(sample):
                print(x)

    def run(self):
        inspectors = [
            ResolveMetadataInspector(),
            EDLInspector(),
            LegacyXMLInspector(),
            FCPXMLInspector(),
            FCPXMLDInspector(),
            FileListInspector(".txt", ".ps1", ".sh"),
        ]
        with InspectorChain(*inspectors, auto_resolve=True) as chain:
            for x in sys.argv[1:]:
                for y in chain.inspect(InspectorInfo(Path(x))):
                    print(y)
