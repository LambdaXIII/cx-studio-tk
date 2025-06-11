from dataclasses import dataclass
from multiprocessing.pool import ThreadPool
from pathlib import Path

from cx_wealth.wealth_label import WealthLabel
from ..filters import ImageFilterChain
from cx_studio.utils import PathUtils
from collections.abc import Sequence
import asyncio
from pydantic import BaseModel, Field, ConfigDict
import ulid
from .format_database import FormatDB


class Mission(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    mission_id: ulid.ULID = Field(default_factory=ulid.new, kw_only=True)

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
        self.target_format_info = (
            FormatDB.search(target_format) if target_format else None
        )
        self.target_suffix = None
        if self.target_format_info:
            self.target_suffix = PathUtils.normalize_suffix(target_format or "").lower()
            if self.target_suffix not in self.target_format_info.extensions:
                self.target_suffix = self.target_format_info.preferred_extension

        self.filter_chain = filter_chain

        self._semaphore = asyncio.Semaphore(10)

    async def make_mission(self, source: Path | str) -> Mission:
        async with self._semaphore:
            source = PathUtils.normalize_path(source)
            target = self.output_dir / source.name
            if self.target_suffix:
                target = PathUtils.force_suffix(target, self.target_suffix)
            return Mission(
                source=source,
                target=target,
                target_format=(
                    self.target_format_info.name if self.target_format_info else None
                ),
                filter_chain=self.filter_chain,
            )

    async def _dispatch_missions(self, sources: Sequence[Path | str]):
        missions = await asyncio.gather(*[self.make_mission(s) for s in sources])
        return [m for m in missions if m is not None]

    def make_missions(self, sources: Sequence[Path | str]) -> list[Mission]:
        return asyncio.run(self._dispatch_missions(sources))
