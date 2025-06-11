from cx_studio.utils import PathUtils
from jpegger.components.format_database import FormatDB
from jpegger.components.mission import Mission
from jpegger.filters import ImageFilterChain
from .simple_appcontext import SimpleAppContext

import asyncio
from collections.abc import Sequence
from pathlib import Path


class SimpleMissionBuilder:
    DEFAULT_SAVING_OPTIONS: dict = {"saveall": True}

    def __init__(
        self,
        filter_chain: ImageFilterChain,
        app_context: SimpleAppContext,
    ):
        self.filter_chain = filter_chain
        self.output_dir = PathUtils.normalize_path(app_context.output_dir or Path.cwd())

        target_format = app_context.format
        self.target_format_info = (
            FormatDB.search(target_format) if target_format else None
        )
        self.target_suffix = None
        if self.target_format_info:
            self.target_suffix = PathUtils.normalize_suffix(target_format or "").lower()
            if self.target_suffix not in self.target_format_info.extensions:
                self.target_suffix = self.target_format_info.preferred_extension

        self.quality = app_context.quality

        self._semaphore = asyncio.Semaphore(10)

    async def make_mission(self, source: Path | str) -> Mission:
        async with self._semaphore:
            source = PathUtils.normalize_path(source)
            target = self.output_dir / source.name
            if self.target_suffix:
                target = PathUtils.force_suffix(target, self.target_suffix)

            options = self.DEFAULT_SAVING_OPTIONS.copy()
            if self.quality:
                options["quality"] = self.quality

            return Mission(
                source=source,
                target=target,
                target_format=(
                    self.target_format_info.name if self.target_format_info else None
                ),
                filter_chain=self.filter_chain,
                saving_options=options,
            )

    async def _dispatch_missions(self, sources: Sequence[Path | str]):
        missions = await asyncio.gather(*[self.make_mission(s) for s in sources])
        return [m for m in missions if m is not None]

    def make_missions(self, sources: Sequence[Path | str]) -> list[Mission]:
        return asyncio.run(self._dispatch_missions(sources))
