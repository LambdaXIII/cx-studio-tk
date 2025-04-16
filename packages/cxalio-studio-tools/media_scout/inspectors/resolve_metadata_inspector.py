from .media_path_inspector import MediaPathInspector, Sample
from collections.abc import AsyncIterable
from typing import IO


class ResolveMetadataInspector(MediaPathInspector):

    @staticmethod
    def _get_headers(fp: IO[bytes]) -> list[str]:
        for line in fp:
            return line.decode().split(",")
        return []

    async def inspect(self, content: bytes) -> AsyncIterable[str]:
        yield "csv"

    async def is_inspectable(self, sample: Sample) -> bool:
        return sample.path.suffix == ".csv"
