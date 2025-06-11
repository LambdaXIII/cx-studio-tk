from dataclasses import dataclass
from multiprocessing.pool import ThreadPool
from pathlib import Path

from cx_wealth.wealth_label import WealthLabel
from ..filters import ImageFilterChain
from cx_studio.utils import PathUtils
from collections.abc import Sequence
import asyncio


@dataclass
class Mission:
    source: Path
    target: Path
    filter_chain: ImageFilterChain = ImageFilterChain([])

    def __rich_label__(self):
        yield "[dim][M][/]"
        yield f"[yellow]{self.source.name}[/yellow]"
        yield "[blue]=>[/]"
        yield f"[yellow]{self.target.name}[/yellow]"
        yield f"[blue]({len(self.filter_chain)} filters)[/blue]"


class SimpleMissionBuilder:
    def __init__(self, filter_chain: ImageFilterChain, output_dir: Path | str | None):
        self.output_dir = PathUtils.normalize_path(output_dir or Path.cwd())
        self.filter_chain = filter_chain
        self._semaphore = asyncio.Semaphore(10)

    async def make_mission(self, source: Path | str) -> Mission:
        async with self._semaphore:
            source = PathUtils.normalize_path(source)
            target = PathUtils.take_dir(source) / source.name
            return Mission(source=source, target=target, filter_chain=self.filter_chain)

    async def make_missions(self, sources: Sequence[Path | str]):
        if not sources:
            return []

        missions = [await self.make_mission(source) for source in sources]
        return missions
