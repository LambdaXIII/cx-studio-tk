from pathlib import Path
from cx_tools_common.app_interface import IApplication
import sys
from .inspectors import ResolveMetadataInspector, MediaPathInspector, InspectorInfo


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
        inspector = ResolveMetadataInspector()
        sample = InspectorInfo(filename)
        if inspector.is_inspectable(sample):
            print("OK")
            for x in inspector.inspect(sample):
                print(x)

    def run(self):
        for x in self.sys_arguments:
            self.probe(Path(x))
