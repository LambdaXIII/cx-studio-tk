import sys, os, io
from pathlib import Path, PurePath
from cx_studio.core import FileSize
from chardet import UniversalDetector


class InspectorInfo:
    def __init__(self, path: os.PathLike):
        self.path = PurePath(path)
        self.size = FileSize(os.path.getsize(path))
        self.encoding: str = "locale"
        self.sample: bytes

        detector = UniversalDetector()
        detector.reset()
        buffer = bytearray()
        with open(path, "rb") as f:
            while not detector.done:
                raw = f.read(io.DEFAULT_BUFFER_SIZE)
                if not raw:
                    break
                detector.feed(raw)
                buffer.extend(raw)
            detector.close()
            self.encoding = detector.result["encoding"] or "locale"
            if len(buffer) < 2048:
                buffer.extend(f.read(1024 - len(buffer)))
            self.sample = bytes(buffer)
