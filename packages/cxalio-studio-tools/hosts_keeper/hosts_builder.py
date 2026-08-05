import asyncio
import locale
import re
from collections.abc import Iterable
from pathlib import Path

from cx_studio.filesystem import detect_file_encoding
from hosts_keeper.i18n import _
from cx_tools.app import IAppComponent, IAppEnvironment
from .appcontext import AppContext
from cx_wealthy import rich_types as r
from .profile import Profile


class HostsBuilder(IAppComponent):
    def __init__(
        self,
        appenv: IAppEnvironment,
        context: AppContext,
        progress: r.Progress,
        hosts_file_path: Path | None = None,
        max_workers: int = -1,
        registered_profile_ids: Iterable[str] = (),
    ):
        super().__init__(appenv, context)
        self.appenv = appenv
        self.context = context
        self._progress = progress
        self.hosts_file_path = hosts_file_path or context.system_hosts_path()
        self.max_workers = max_workers if max_workers > 0 else context.max_workers
        self._semaphore = asyncio.Semaphore(self.max_workers)
        # 已注册（存在配置文件）的 profile id 集合，用于识别 hosts 中的残留标记块。
        # 仅作为检测判定依据，不影响标记识别与清除行为（见 prepare_custom_lines 的决策注释）。
        self.registered_profile_ids: set[str] = set(registered_profile_ids)

    PROFILE_START_MARKER = re.compile(Profile.PROFILE_START_MARKER_PATTERN)
    PROFILE_END_MARKER = re.compile(Profile.PROFILE_END_MARKER_PATTERN)

    def _report_orphan_marker(self, marker: str, missing: str) -> None:
        """汇报孤立标记（有 START 无 END / 有 END 无 START）。

        决策（格式即契约）：`##### <id> START/END #####` 是 hostskeeper 的保留标记
        格式，命中即按 profile 块处理。标记不配对是操作者破坏了 hosts 文件的结构
        ——工具只汇报、不自动修复，由用户自行检查处理。
        """
        self.appenv.say(
            f"[cx.warning]{_('检测到 hosts 结构异常：标记 {marker} 缺少配对的 {missing} 标记。请检查 hosts 文件。').format(marker=marker, missing=missing)}"
        )

    def _report_unregistered_block(self, profile_id: str) -> None:
        """汇报未注册标记块（对应 profile 已删除/改名）。

        检测仅汇报：块内容仍按契约清除（两个标记之间为 profile 领地、重建时整体
        覆盖），报告只是让「删除 profile 已生效」对用户可见。
        """
        self.appenv.say(
            f"[cx.warning]{_('已清除残留标记块 {profile_id}（对应配置文件不存在或已改名）。').format(profile_id=profile_id)}"
        )

    async def prepare_custom_lines(self) -> list[str]:
        async with self._semaphore:
            result = []
            encoding = detect_file_encoding(
                self.hosts_file_path
            ) or locale.getpreferredencoding(False)
            # 深度计数（而非布尔）容忍嵌套标记：嵌套 START 使领地持续，其对应的
            # END 不会误报孤立（嵌套本身违反契约、属操作者责任，仅做到不误报）。
            profile_depth: int = 0
            orphan_start_id: str | None = None
            unregistered_blocks: set[str] = set()
            with self.hosts_file_path.open("r", encoding=encoding) as f:
                for line in f:
                    striped_line = line.strip()
                    start_match = self.PROFILE_START_MARKER.match(striped_line)
                    if start_match is not None:
                        # 契约：命中保留标记格式即按 profile 块处理
                        profile_depth += 1
                        orphan_start_id = start_match.group(1).strip()
                        if orphan_start_id not in self.registered_profile_ids:
                            unregistered_blocks.add(orphan_start_id)
                        continue
                    end_match = self.PROFILE_END_MARKER.match(striped_line)
                    if end_match is not None:
                        if profile_depth == 0:
                            # 孤立 END（无配对的 START）：仅汇报，处理行为不变
                            self._report_orphan_marker(
                                f"##### {end_match.group(1).strip()} END #####",
                                "START",
                            )
                        else:
                            profile_depth -= 1
                            if profile_depth == 0:
                                orphan_start_id = None
                        continue
                    if profile_depth == 0 and striped_line:
                        result.append(striped_line)
            if orphan_start_id is not None:
                # 孤立 START（无配对的 END）：START 后至文件尾视为 profile 内容，
                # 处理行为不变，仅汇报。discard 避免对同一标记块同时报告「孤立」
                # 与「未注册」双重报警（孤立消息已含标记 id）。
                unregistered_blocks.discard(orphan_start_id)
                self._report_orphan_marker(
                    f"##### {orphan_start_id} START #####", "END"
                )
            for profile_id in sorted(unregistered_blocks):
                self._report_unregistered_block(profile_id)
            return result

    async def prepare_profile_lines(self, profile: Profile) -> list[str]:
        async with self._semaphore:
            # 统计 contenter 数量以决定进度模式（与 Profile.async_iter_records 的收集逻辑一致）
            contenter_count = profile.count_contenters()
            task_id = self._progress.add_task(
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
                        self._progress.update(
                            task_id, description=desc, completed=current - 1
                        )
                    else:
                        self._progress.update(
                            task_id, description=contenter.status_text
                        )

                async for line in profile.async_iter_lines(
                    on_contenter_status=on_contenter_status,
                    pretend_delay=4.0 if self.context.pretending_mode else None,
                    appenv=self.appenv,
                ):
                    result.append(line)
                # 完成
                if contenter_count > 1:
                    self._progress.update(
                        task_id,
                        description=f"[cx.success]{profile.name} ✓[/]",
                        completed=contenter_count,
                    )
                else:
                    self._progress.update(
                        task_id,
                        description=f"[cx.success]{profile.name} ✓[/]",
                        total=1,
                        completed=1,
                    )
                self.appenv.say(
                    f"[cx.success]{_('已处理配置文件 {name}').format(name=profile.name)}[/]"
                )
            except Exception as e:
                self._progress.update(
                    task_id,
                    description=f"[cx.error]{profile.name} ✗ {e}[/]",
                )
                raise
            finally:
                self._progress.stop_task(task_id)
            return result

    async def async_build_lines(self, profiles: Iterable[Profile]) -> list[list[str]]:
        # 输出顺序决策：custom 区最前（域名受保护、绝不覆盖）→ profiles 按
        # priority 降序。sorted() 是稳定排序：相同 priority 的 profile 保持
        # 发现顺序，不引入 tie-break（顺序不确定性是接受的）。
        profiles = sorted(profiles, key=lambda profile: profile.priority, reverse=True)
        tasks = [asyncio.create_task(self.prepare_custom_lines())]
        for profile in profiles:
            tasks.append(asyncio.create_task(self.prepare_profile_lines(profile)))
        return await asyncio.gather(*tasks)

    @staticmethod
    def _dedup_key(line: str) -> tuple[str, ...] | None:
        """提取 hosts 记录行的查重键（规范化域名集合），非记录行返回 None。

        决策（first match wins）：与平台 hosts 解析行为一致——Linux（glibc）与
        Windows（DNS Client）均以首个匹配生效，不存在「覆盖」。查重按域名逐个
        判定且大小写不敏感：一行内多个域名分别参与查重，任一域名已出现即整行
        视为冲突。

        注意：不能沿用 HostRecord.from_line 的解析——它对行内注释
        （`1.2.3.4 example.com # foo`）会把 `#`/`foo` 当作域名。
        """
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return None
        tokens = stripped.split()
        if len(tokens) < 2:
            return None
        domains: list[str] = []
        for token in tokens[1:]:
            if token.startswith("#"):
                break
            domains.append(token.lower())
        return tuple(domains) if domains else None

    def iter_lines(self, profiles: Iterable[Profile]) -> Iterable[str]:
        collection = asyncio.run(self.async_build_lines(profiles))
        # 查重决策：后出现者以 `# ` 注释保留在自身块内（不静默删除、不标注来源）。
        # 注释行是生成产物——每次 update 全量重新生成，冲突消失（如高优先级
        # profile 被禁用）后自动恢复为有效行。
        seen: set[str] = set()
        for lines in collection:
            for line in lines:
                keys = self._dedup_key(line)
                if keys is not None:
                    if any(key in seen for key in keys):
                        yield f"# {line}"
                        continue
                    seen.update(keys)
                yield line
