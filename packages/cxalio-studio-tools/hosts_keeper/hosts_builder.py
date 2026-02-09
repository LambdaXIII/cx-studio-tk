from collections.abc import AsyncGenerator, Iterable
from pathlib import Path
from .profile import Profile
import os, sys
from cx_studio.utils import EncodingUtils
import re
import asyncio
from .appenv import appenv
from cx_studio.utils import FunctionalUtils


class HostsBuilder:
    def __init__(self, hosts_file_path: Path | None = None, max_workers: int = -1):
        self.hosts_file_path = hosts_file_path or appenv.system_hosts_path()
        self.max_workers = (
            max_workers if max_workers > 0 else appenv.context.max_workers
        )
        self._semaphore = asyncio.Semaphore(self.max_workers)

    PROFILE_START_MARKER = re.compile(Profile.PROFILE_START_MARKER_PATTERN)
    PROFILE_END_MARKER = re.compile(Profile.PROFILE_END_MARKER_PATTERN)

    async def prepare_customed_lines(self) -> list[str]:
        async with self._semaphore:
            result = []
            encoding = EncodingUtils.detect_encoding(self.hosts_file_path)
            profile_entered: bool = False
            with self.hosts_file_path.open("r", encoding=encoding) as f:
                for line in f.readlines():
                    await asyncio.sleep(0)
                    if self.PROFILE_START_MARKER.match(line):
                        profile_entered = True
                        continue
                    if self.PROFILE_END_MARKER.match(line):
                        profile_entered = False
                        continue
                    if not profile_entered:
                        striped_line = line.strip()
                        if len(striped_line) > 0:
                            result.append(striped_line)
        return result

    async def prepare_profile_lines(self, profile: Profile) -> list[str]:
        async with self._semaphore:
            result = []
            async for line in profile.async_iter_lines():
                result.append(line)
        return result

    async def async_build_lines(self, profiles: Iterable[Profile]) -> list[list[str]]:
        tasks = [asyncio.create_task(self.prepare_customed_lines())]
        for profile in profiles:
            tasks.append(asyncio.create_task(self.prepare_profile_lines(profile)))
        return await asyncio.gather(*tasks)

    def iter_lines(self, profiles: Iterable[Profile]) -> Iterable[str]:
        collection = asyncio.run(self.async_build_lines(profiles))
        yield from FunctionalUtils.flatten_list(*collection)
