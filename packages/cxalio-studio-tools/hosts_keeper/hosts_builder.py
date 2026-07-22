import asyncio
import locale
import re
from collections.abc import Iterable
from pathlib import Path

from cx_studio.collectiontools import flatten_list
from cx_studio.filesystem import detect_file_encoding
from hosts_keeper.i18n import _
from .appenv import appenv
from .profile import Profile


class HostsBuilder:
    def __init__(self, hosts_file_path: Path | None = None, max_workers: int = -1):
        self.hosts_file_path = hosts_file_path or appenv.system_hosts_path()
        self.max_workers = (
            max_workers if max_workers > 0 else appenv.context.max_workers
        )
        self._semaphore = asyncio.Semaphore(self.max_workers)

    PROFILE_START_MARKER = re.compile(Profile.PROFILE_START_MARKER_PATTERN)
    PROFILE_END_MARKER = re.compile(Profile.PROFILE_END_MARKER_PATTERN)

    async def prepare_custom_lines(self) -> list[str]:
        async with self._semaphore:
            result = []
            encoding = detect_file_encoding(
                self.hosts_file_path
            ) or locale.getpreferredencoding(False)
            profile_entered: bool = False
            with self.hosts_file_path.open("r", encoding=encoding) as f:
                for line in f:
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
            # 统计 contenter 数量以决定进度模式（与 Profile.async_iter_records 的收集逻辑一致）
            contenter_count = profile.count_contenters()
            task_id = appenv.progress.add_task(
                profile.name,
                total=contenter_count if contenter_count > 1 else None,
            )
            result = []
            try:

                def on_contenter_status(contenter, current, total):
                    if total > 1:
                        desc = (
                            f"[bright_black]({current}/{total})[/]"
                            f" {contenter.status_text}"
                        )
                        appenv.progress.update(
                            task_id, description=desc, completed=current - 1
                        )
                    else:
                        appenv.progress.update(
                            task_id, description=contenter.status_text
                        )

                async for line in profile.async_iter_lines(
                    on_contenter_status=on_contenter_status,
                    pretend_delay=4.0 if appenv.context.pretending_mode else None,
                ):
                    result.append(line)
                # 完成
                if contenter_count > 1:
                    appenv.progress.update(
                        task_id,
                        description=f"[cx.success]{profile.name} ✓[/]",
                        completed=contenter_count,
                    )
                else:
                    appenv.progress.update(
                        task_id,
                        description=f"[cx.success]{profile.name} ✓[/]",
                        total=1,
                        completed=1,
                    )
                appenv.say(
                    f"[cx.success]{_('已处理配置文件 {name}').format(name=profile.name)}[/]"
                )
            except Exception as e:
                appenv.progress.update(
                    task_id,
                    description=f"[cx.error]{profile.name} ✗ {e}[/]",
                )
                raise
            finally:
                appenv.progress.stop_task(task_id)
            return result

    async def async_build_lines(self, profiles: Iterable[Profile]) -> list[list[str]]:
        tasks = [asyncio.create_task(self.prepare_custom_lines())]
        for profile in profiles:
            tasks.append(asyncio.create_task(self.prepare_profile_lines(profile)))
        return await asyncio.gather(*tasks)

    def iter_lines(self, profiles: Iterable[Profile]) -> Iterable[str]:
        collection = asyncio.run(self.async_build_lines(profiles))
        yield from flatten_list(*collection)
