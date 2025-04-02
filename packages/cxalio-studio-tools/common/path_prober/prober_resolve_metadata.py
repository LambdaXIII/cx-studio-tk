from io import TextIOBase
from typing import Generator

from .path_prober import IPathProber
from pathlib import Path,PurePath
from cx_studio.utils import EncodingUtils
import csv


class ResolveMetadataCSVProber(IPathProber):
    @staticmethod
    def _get_headers(fp:TextIOBase)->list[str]:
        cursor = fp.tell()
        fp.seek(0)
        result = []
        for line in fp:
            if line.strip()!= "":
                result = line.split(',')
                break
        fp.seek(cursor)
        return []

    def is_acceptable(self,fp:TextIOBase) ->bool:
        suffix = self._get_suffix(fp)
        if suffix is not None and suffix != ".csv":
            return False

        headers = self._get_headers(fp)
        return "File Name" in headers and "Clip Directory" in headers

    def probe(self,fp:TextIOBase) ->Generator[PurePath]:
        cursor = fp.tell()
        headers = self._get_headers(fp)
        fp.seek(0)
        reader = csv.DictReader(fp,fieldnames=headers)
        for row in reader:
            name = row["File Name"]
            folder = row["Clip Directory"]
            if name=="File Name" or folder == "Clip Directory":
                continue
            yield PurePath(folder,name)
        fp.seek(cursor)

