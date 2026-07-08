"""media_killer CLI Application。

对接 CLI_BEHAVIOR.md 定义的用户侧行为，编排 Preset 加载、源文件展开、
Mission 生成、排序去重、脚本保存与执行调度。

实现范围：help/tutorial/generate/mission 生成/脚本保存/模拟运行/实际转码。
"""

from __future__ import annotations

import asyncio
import importlib.resources
import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import override

from cx_studio.core.cx_time import CxTime
from cx_studio.core.cx_filesize import FileSize
from cx_studio.filesystem import PathUtils
from cx_tools.app import IApplication, SafeError, try_open_text_file
from cx_tools.i18n import _
from cx_wealthy import IndexedListPanel, WealthDetailPanel
from rich.progress import TaskID

from .appenv import appenv
from .appcontext import OVERWRITE_DANGER, OVERWRITE_SAFE
from .app_help import AppHelp
from .components import (
    DebugReporter,
    MissionMaker,
    MissionScheduler,
    MissionStore,
    Preset,
    PresetLoader,
    ScriptMaker,
    SourceExpander,
)
from .media import (
    ExecutorStatus,
    Mission,
    MissionExecutor,
    MissionPretender,
    MissionResult,
)


class Application(IApplication):
    """media_killer CLI 应用。"""

    def __init__(self, arguments: Sequence[str] | None = None) -> None:
        super().__init__(arguments or sys.argv[1:])
        self.presets: list[Preset] = []
        self.sources: list[Path] = []
        self.missions: list[Mission] = []

    @override
    def start(self) -> None:
        appenv.load_arguments(self.sys_arguments)
        appenv.start()
        appenv.show_banner()

    @override
    def stop(self) -> None:
        if not appenv.context.continue_mode:
            self._save_missions(self.missions)
        appenv.stop()

    @override
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            appenv.whisper(_("程序正常退出。"))
        elif exc_type is SafeError:
            appenv.say(exc_val)
            result = True
        return result

    # --- 静态工具方法 ---

    @staticmethod
    def _is_preset(path: Path) -> bool:
        """判断输入项是否为预设文件（CLI_BEHAVIOR.md §4.1）。"""
        if path.suffix.lower() == ".toml":
            return True
        if path.suffix == "":
            return path.with_suffix(".toml").exists()
        return False

    @staticmethod
    def _save_missions(missions: Iterable[Mission]) -> None:
        """保存 Mission 列表供 -c/--continue 使用。"""
        store = MissionStore()
        store.save(appenv.config_manager.get_file("last_missions.xml"), missions)

    @staticmethod
    def _load_missions() -> list[Mission]:
        """加载上次保存的 Mission 列表。"""
        path = appenv.config_manager.get_file("last_missions.xml")
        if not path.exists():
            return []
        store = MissionStore()
        return store.load(path)

    @staticmethod
    def export_example_preset(filename: Path) -> None:
        """导出示例预设文件。"""
        filename = Path(PathUtils.force_suffix(filename, ".toml"))

        if filename.exists():
            if appenv.context.overwrite_mode == OVERWRITE_DANGER:
                appenv.say(
                    f"[dim red]{_('文件 {name} 已存在，将强制覆盖。').format(name=filename)}[/]"
                )
            else:
                appenv.say(
                    f"[cx.warning]{_('文件 {name} 已存在，跳过覆盖。').format(name=filename)}[/]"
                )
                return

        with importlib.resources.open_text("media_killer", "example_preset.toml") as f:
            content = f.read()
        filename.write_text(content, encoding="utf-8")
        appenv.say(f"{_('已生成示例预设文件:')} [cx.filepath]{filename}[/]")

    @staticmethod
    def _open_in_editor(path: Path) -> None:
        """如果有可用编辑器，打开指定文件供用户编辑。静默失败。"""
        try_open_text_file(path)

    # --- Mission 整理 ---

    def _sort_and_dedup_missions(self, missions: list[Mission]) -> list[Mission]:
        """按 (source, preset_id) 去重，按 sort_mode 排序。"""
        seen: set[tuple[Path, str | None]] = set()
        unique: list[Mission] = []
        for m in missions:
            key = (m.source, m.preset_id)
            if key not in seen:
                seen.add(key)
                unique.append(m)

        sort_mode = appenv.context.sort_mode
        if sort_mode == "source":
            unique.sort(key=lambda m: str(m.source))
        elif sort_mode == "preset":
            unique.sort(key=lambda m: m.preset_name or "")
        elif sort_mode == "target":
            unique.sort(key=lambda m: str(m.standard_target))
        # "x" 保持输入顺序

        return unique

    # --- Mission 执行 ---

    def _execute_missions(self, pretend: bool) -> None:
        """构造调度器并执行 Mission 列表。

        Args:
            pretend: True 表示模拟运行（MissionPretender），False 表示实际转码（MissionExecutor）。
        """
        ctx = appenv.context

        # 构造 executor_factory（不同内名避免 Pylance 重声明警告）
        if pretend:

            def _pretend_factory(mission: Mission) -> MissionPretender:
                duration = self._lookup_duration(mission)
                return MissionPretender(mission, duration=duration)

            executor_factory = _pretend_factory

        else:

            def _execute_factory(mission: Mission) -> MissionExecutor:
                return MissionExecutor(mission)

            executor_factory = _execute_factory

        scheduler = MissionScheduler(
            missions=self.missions,
            max_workers=ctx.max_workers,
            executor_factory=executor_factory,
        )

        # 挂接第一次中断回调（取消所有正在运行的 executor，pending 不受影响）
        @appenv.interrupt_handler.on("first_triggered")
        def _on_first() -> None:
            scheduler.cancel_running()

        # 挂接第二次中断回调（取消所有任务，含 pending）
        @appenv.interrupt_handler.on("second_triggered")
        def _on_second() -> None:
            scheduler.cancel_all()

        # 挂接进度 UI
        task_ids: dict[int, TaskID] = {}
        total = len(self.missions)

        @scheduler.on("mission_started")
        def _on_started(index: int, status: ExecutorStatus) -> None:
            mission = self.missions[index]
            short_id = status.mission_id[:6]
            # 输出 Mission 详情面板（whisper，仅 --debug 可见；面板在进度条之前）
            appenv.whisper(
                WealthDetailPanel(
                    mission,
                    title=f"[bright_black]M[/] [dim green]{short_id}[/] [{index + 1}/{total}] {mission.name}",
                )
            )
            duration = self._lookup_duration(mission)
            task_id = appenv.progress.add_task(
                f"[bright_black][{index + 1}/{total}][/] [cx.mk.mission.name]{mission.name}[/]",
                total=duration.total_seconds if duration else None,
            )
            task_ids[index] = task_id

        @scheduler.on("mission_progress_updated")
        def _on_progress(
            index: int, current: CxTime, total_time: CxTime | None
        ) -> None:
            tid = task_ids.get(index)
            if tid is not None:
                appenv.progress.update(tid, completed=current.total_seconds)

        @scheduler.on("mission_finished")
        def _on_finished(index: int, status: ExecutorStatus) -> None:
            tid = task_ids.pop(index, None)
            if tid is not None:
                appenv.progress.remove_task(tid)
            result = scheduler.results.get(index, MissionResult.FAILED)
            self._report_mission_result(self.missions[index], result)

        # 挂接诊断输出（executor 内部步骤 whisper）
        DebugReporter(scheduler, appenv).attach()

        # 执行
        results = asyncio.run(scheduler.run())

        # 统计
        self._report_summary(results)

    def _lookup_duration(self, mission: Mission) -> CxTime | None:
        """从 MediaDB 查询源文件时长。

        Args:
            mission: 要查询的 Mission

        Returns:
            CxTime 时长，查询失败返回 None
        """
        info = appenv.media_db.get_media_info(mission.source)
        if info is not None and info.duration is not None:
            return CxTime.from_seconds(info.duration)
        return None

    @staticmethod
    def _report_mission_result(mission: Mission, result: MissionResult) -> None:
        """输出单个 Mission 的结果文字行（旧版 make_line_report 风格）。

        格式：[M] [n→m] 任务名 ........ 状态（左对齐任务名 + 右对齐状态）

        Args:
            mission: 已完成的 Mission
            result: 执行结果
        """
        from rich.text import Text
        from rich.columns import Columns

        header = f"[bright_black]M[/] [dim green][{len(mission.inputs)}->{len(mission.outputs)}][/] "
        name_part = f"[cx.mk.mission.name]{mission.name}[/]"
        label = header + name_part

        if result == MissionResult.SUCCESS:
            right_str = f"[cx.mk.status.success]{_('完成')}[/]"
        elif result == MissionResult.FAILED:
            right_str = f"[cx.mk.status.failed]{_('运行异常')}[/]"
        elif result == MissionResult.CANCELED:
            right_str = f"[cx.mk.status.canceled]{_('被取消')}[/]"
        elif result == MissionResult.SKIPPED:
            right_str = f"[dim]{_('已跳过')}[/]"
        else:
            right_str = f"[dim]{result.value}[/]"

        left = Text.from_markup(label, justify="left", overflow="ellipsis")
        left.no_wrap = True
        right = Text.from_markup(right_str, justify="right")
        appenv.say(Columns([left, right], expand=True))

    def _report_summary(self, results: list[MissionResult]) -> None:
        """输出批量执行统计。

        Args:
            results: 所有 Mission 的执行结果
        """
        counts = Counter(results)

        if n := counts.get(MissionResult.SUCCESS, 0):
            appenv.say(_("成功执行 {n} 个任务。").format(n=n))
        if n := counts.get(MissionResult.FAILED, 0):
            appenv.say(_("{n} 个任务失败。").format(n=n))
        if n := counts.get(MissionResult.CANCELED, 0):
            appenv.say(_("{n} 个任务取消。").format(n=n))
        if n := counts.get(MissionResult.SKIPPED, 0):
            appenv.say(_("{n} 个任务跳过。").format(n=n))

        # 文件统计（来自调度器实时收集的清单）
        processed = appenv.processed_files
        generated = appenv.generated_files
        if processed:
            size = FileSize(sum(f.stat().st_size for f in processed))
            appenv.say(
                _("处理 {n} 个文件（共 {size}）。").format(
                    n=len(processed), size=size.pretty_string
                )
            )
        if generated and len(generated) != len(processed):
            size = FileSize(sum(f.stat().st_size for f in generated))
            appenv.say(
                _("生成 {n} 个文件（共 {size}）。").format(
                    n=len(generated), size=size.pretty_string
                )
            )

    # --- 主流程 ---

    def run(self) -> None:
        ctx = appenv.context

        # 1. help / tutorial
        if ctx.show_help:
            AppHelp.show_help(appenv.console)
            return
        if ctx.show_full_help:
            AppHelp.show_full_help(appenv.console)
        # 2. generate
        if ctx.generate:
            generated: list[Path] = []
            targets = [ctx.generate]
            targets.extend(ctx.inputs)
            for s in targets:
                p = Path(s)
                if p.suffix == ".toml" or p.suffix == "":
                    resolved = Path(PathUtils.force_suffix(p, ".toml"))
                    self.export_example_preset(p)
                    generated.append(resolved)
                else:
                    appenv.whisper(f"{p} {_('并非合法的文件名，不予处理。')}")
            for p in generated:
                self._open_in_editor(p)
            return

        # 3. 校验输入
        if not ctx.inputs:
            raise SafeError(_("未提供任何输入项，请使用 -h 查看帮助。"))

        # 4. 扫描输入项，区分 preset / source
        for raw in ctx.inputs:
            p = Path(raw)
            if self._is_preset(p):
                try:
                    preset = PresetLoader().load(p.resolve())
                except SafeError:
                    raise
                except Exception as e:
                    raise SafeError(
                        _("加载预设文件 {path} 失败: {err}").format(path=p, err=e)
                    )
                self.presets.append(preset)
                # 输出 Preset 详情面板（whisper，仅 --debug 可见）
                appenv.whisper(
                    WealthDetailPanel(
                        preset,
                        title=f"{_('预设')} [cx.mk.preset.name]{preset.name}[/]",
                    )
                )
                appenv.whisper(f"[cyan]{_('配置文件路径')}[/] [cx.filepath]{p}[/]")
            else:
                self.sources.append(p)
                appenv.whisper(f"[green]{_('媒体来源路径')}[/] [cx.filepath]{p}[/]")

        if self.presets:
            appenv.say(
                _(
                    "已添加 {preset_count} 个配置文件和 {source_count} 个来源路径。"
                ).format(preset_count=len(self.presets), source_count=len(self.sources))
            )

        if not self.presets:
            raise SafeError(_("未提供任何预设文件。"))

        # 5. 合并 source_suffixes，构造 SourceExpander
        merged_suffixes: set[str] = set()
        for preset in self.presets:
            merged_suffixes |= preset.source_suffixes

        from media_scout.inspectors import (
            ResolveMetadataInspector,
            EDLInspector,
            LegacyXMLInspector,
            FCPXMLInspector,
            FCPXMLDInspector,
            InspectorChain,
        )
        from media_scout.inspectors.filelist_inspector import FileListInspector

        scout_chain = InspectorChain(
            ResolveMetadataInspector(),
            EDLInspector(),
            LegacyXMLInspector(),
            FCPXMLInspector(),
            FCPXMLDInspector(),
            FileListInspector(".txt", ".ps1", ".sh"),
        )
        expander = SourceExpander(suffixes=merged_suffixes, scout_chain=scout_chain)

        # 6. 展开源文件
        expanded_sources = list(expander.expand(*self.sources))
        for src in self.sources:
            resolved = Path(src).resolve()
            if not resolved.exists():
                raise SafeError(_("源文件不存在: {path}").format(path=src))

        # 7. 生成 Mission
        output_dir = None
        if ctx.output_dir:
            output_dir = Path(ctx.output_dir).resolve()
            appenv.say(f"{_('输出目录将被替换为:')} [cx.filepath]{output_dir}[/]")

        current_missions: list[Mission] = []
        for preset in self.presets:
            maker = MissionMaker(preset)
            for source in expanded_sources:
                mission = maker.make_mission(
                    source=source,
                    output_dir=output_dir,
                    overwrite_mode=ctx.overwrite_mode,
                )
                current_missions.append(mission)

        if current_missions:
            appenv.say(_("生成了 {count} 个任务。").format(count=len(current_missions)))

        # 8. continue 叠加
        all_missions = list(current_missions)
        if ctx.continue_mode:
            last = self._load_missions()
            appenv.say(_("从上次执行中恢复了 {count} 个任务……").format(count=len(last)))
            all_missions.extend(last)

        # 9. 排序去重
        self.missions = self._sort_and_dedup_missions(all_missions)

        if not self.missions:
            appenv.say(_("没有任务需要执行。"))
            return

        appenv.say(_("本次执行共 {n} 个任务。").format(n=len(self.missions)))
        appenv.whisper(IndexedListPanel(self.missions, _("整理完的任务列表")))

        # 10. 脚本保存
        if ctx.save_script:
            script_path = Path(ctx.save_script)
            if script_path.exists() and ctx.overwrite_mode == OVERWRITE_SAFE:
                raise SafeError(
                    _("脚本文件 {name} 已存在，请取消 --no-overwrite 选项。").format(
                        name=script_path
                    )
                )
            ScriptMaker(self.missions).save(script_path)
            return

        # 11. 模拟运行
        if ctx.pretending_mode:
            appenv.say(
                f"[dim]{_('检测到[italic cyan underline]假装模式[/]，将不会真正执行任何操作。')}[/]"
            )
            self._execute_missions(pretend=True)
            return

        # 12. 实际转码
        self._execute_missions(pretend=False)
