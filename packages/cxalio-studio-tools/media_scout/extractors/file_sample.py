import os
from pathlib import Path


class FileSample:
    def __init__(self, filename: os.PathLike):
        self.filename = Path(filename)
        self.sample: bytes
