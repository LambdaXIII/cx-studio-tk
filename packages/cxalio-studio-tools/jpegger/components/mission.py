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
    target_format: str | None
    filter_chain: ImageFilterChain = ImageFilterChain([])

    def __rich_label__(self):
        yield (
            f"[yellow][{self.target_format.upper()}][/]"
            if self.target_format
            else "[dim][M][/]"
        )
        yield f"[yellow]{self.source.name}[/yellow]"
        yield "[blue]=>[/]"
        yield f"[yellow]{self.target.name}[/yellow]"
        yield f"[blue]({len(self.filter_chain)} filters)[/blue]"


class SimpleMissionBuilder:
    def __init__(
        self,
        filter_chain: ImageFilterChain,
        output_dir: Path | str | None,
        target_format: str | None = None,
    ):
        self.output_dir = PathUtils.normalize_path(output_dir or Path.cwd())
        self.target_format = target_format
        self.filter_chain = filter_chain
        self._semaphore = asyncio.Semaphore(10)

    async def make_mission(self, source: Path | str) -> Mission:
        async with self._semaphore:
            source = PathUtils.normalize_path(source)
            target = PathUtils.take_dir(source) / source.name
            if self.target_format:
                target = PathUtils.force_suffix(target, self.target_format)
            return Mission(
                source=source,
                target=target,
                target_format=self.target_format,
                filter_chain=self.filter_chain,
            )

    async def _dispatch_missions(self, sources: Sequence[Path | str]):
        missions = await asyncio.gather(*[self.make_mission(s) for s in sources])
        return [m for m in missions if m is not None]

    def make_missions(self, sources: Sequence[Path | str]) -> list[Mission]:
        return asyncio.run(self._dispatch_missions(sources))
