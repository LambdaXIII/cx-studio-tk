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
from datetime import datetime
from pathlib import Path
from typing import override

from cx_studio.core.cx_time import CxTime
from cx_studio.filesystem import FileList, PathUtils
from cx_tools.app import (
    IApplication,
    IAppEnvironment,
    SafeError,
    run_async,
    try_open_text_file,
)
from media_killer.i18n import _
from cx_wealthy import IndexedListPanel, WealthyDetailPanel, rich_types as r

from .appcontext import OVERWRITE_DANGER, OVERWRITE_SAFE, AppContext
from .appenv import AppEnv
from .app_help import MediaKillerHelp
from .components import (
    MissionMaker,
    MissionStore,
    Preset,
    PresetLoader,
    ScriptMaker,
    SourceExpander,
)
from .media import (
    FileLogType,
    Mission,
    MissionHQ,
    MissionResult,
)
from .media.mission_hq import MISSION_FILE_LOGGED, MISSION_RESULT, MISSION_STARTED


class MediaKillerApp(IApplication):
    """media_killer CLI 应用。"""

    def __init__(
        self,
        appenv: IAppEnvironment,
        context: AppContext,
        progress: r.Progress,
    ) -> None:
        super().__init__(appenv, context)
        self.context = context
        self.progress = progress
        self.presets: list[Preset] = []
        self.sources: list[Path] = []
        self.missions: list[Mission] = []
        self._app_start_time: datetime | None = None

    @override
    def start(self) -> None:
        self.appenv.set_debug_mode(self.context.debug_mode)
        # 显示 banner
        banners = []
        with importlib.resources.open_text("media_killer", "banner.txt") as f:
            banner_text = r.Text(
                f.read(),
                style="cx.mk.banner",
                no_wrap=True,
                overflow="crop",
                justify="center",
            )
            banners.append(r.Align.center(banner_text))
        version_info = r.Text.from_markup(
            f"[cx.info]{self.appenv.app_name}[/] [cx.number]v{self.appenv.app_version}[/]"
        )
        banners.append(r.Align.center(version_info))
        description = r.Text(_("媒体文件批量转码工具"), style="cx.debug")
        tags = []
        if self.context.pretending_mode:
            tags.append(f"[cx.info]{_('模拟运行')}[/]")
        mode = self.context.overwrite_mode
        if mode == OVERWRITE_SAFE:
            tags.append(f"[cx.success]{_('安全模式启动，将拒绝任何覆盖操作')}[/]")
        elif mode == OVERWRITE_DANGER:
            tags.append(f"[cx.error]{_('覆盖模式已启动，将自动覆盖任何输出')}[/]")
        if tags:
            description = r.Text.from_markup(" · ".join(tags))
        banners.append(r.Align.center(description))
        self.appenv.say(r.Group(*banners))
        self._app_start_time = datetime.now()

    @override
    def stop(self) -> None:
        if not self.context.continue_mode:
            self._save_missions(self.missions)

        # 输出文件统计报告（从 _report_file_list 逻辑迁移）
        text = self._report_file_list(
            self.context.processed_files, _("本次执行处理了 {n} 个文件")
        )
        if text:
            self.appenv.say(text)
        text = self._report_file_list(
            self.context.generated_files, _("本次执行生成了 {n} 个文件")
        )
        if text:
            self.appenv.say(text)

        # garbage 清理
        ctx = self.context
        if len(ctx.garbage_files) > 0:
            self.appenv.say(f"[cx.error]{_('正在清理失败的目标文件...')}[/]")
            for filename in ctx.garbage_files:
                self.appenv.whisper(f"[cx.filepath]{filename}[/]")
            count = len(ctx.garbage_files)
            ctx.cleanup()
            self.appenv.say(
                f"[cx.error]{_('清理了 {n} 个失败的目标文件').format(n=count)}[/]"
            )

        # 输出耗时统计（超过 5 秒）
        if self._app_start_time is not None:
            time_spent = datetime.now() - self._app_start_time
            if time_spent.total_seconds() > 5:
                self.appenv.say(
                    _("总共耗时 {time_str}。").format(
                        time_str=CxTime.from_seconds(
                            time_spent.total_seconds()
                        ).pretty_string
                    )
                )

    @override
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            self.appenv.whisper(_("程序正常退出。"))
        elif exc_type is SafeError:
            self.appenv.say(exc_val)
            result = True
        return result

    # --- 静态工具方法 ---

    @staticmethod
    def _resolve_preset(path: Path) -> Path | None:
        """将用户输入解析为预设文件的实际路径。

        若为 .toml 文件直接返回；若无扩展名则尝试补全 .toml 后缀，
        或使用原路径（当文件以无扩展名形式存在时）。
        无法解析为实际存在的文件时返回 None。
        """
        if path.suffix.lower() == ".toml":
            return path
        if path.suffix == "":
            resolved = path.with_suffix(".toml")
            if resolved.exists():
                return resolved
            if path.exists():
                return path
        return None

    def _save_missions(self, missions: Iterable[Mission]) -> None:
        """保存 Mission 列表供 -c/--continue 使用。"""
        store = MissionStore()
        store.save(self.context.config_manager.get_file("last_missions.xml"), missions)

    def _load_missions(self) -> list[Mission]:
        """加载上次保存的 Mission 列表。"""
        path = self.context.config_manager.get_file("last_missions.xml")
        if not path.exists():
            return []
        store = MissionStore()
        return store.load(path)

    def export_example_preset(self, filename: Path) -> None:
        """导出示例预设文件。"""
        filename = Path(PathUtils.force_suffix(filename, ".toml"))

        if filename.exists():
            if self.context.overwrite_mode == OVERWRITE_DANGER:
                self.appenv.say(
                    f"[cx.error]{_('文件 {name} 已存在，将强制覆盖。').format(name=filename)}[/]"
                )
            else:
                self.appenv.say(
                    f"[cx.warning]{_('文件 {name} 已存在，跳过覆盖。').format(name=filename)}[/]"
                )
                return

        with importlib.resources.open_text("media_killer", "example_preset.toml") as f:
            content = f.read()
        filename.write_text(content, encoding="utf-8")
        self.appenv.say(f"{_('已生成示例预设文件:')} [cx.filepath]{filename}[/]")

    @staticmethod
    def _open_in_editor(path: Path) -> None:
        """如果有可用编辑器，打开指定文件供用户编辑。静默失败。"""
        try_open_text_file(path)

    # --- 文件统计报告 ---

    @staticmethod
    def _report_file_list(file_list: FileList, msgid: str) -> str | None:
        """输出单个文件列表的统计报告（一行）。

        文件数为 0 时整句不输出。文件数 > 0 但总大小为 0 时
        仅输出计数句，不带括号大小部分。文件数和大小均 > 0 时
        输出 '文案（大小）' 格式。

        注意：此方法不直接输出（Application 不持有 self.appenv 的输出方法），
        由调用方自行输出。

        Args:
            file_list: 要报告的 FileList
            msgid: 带 {n} 占位符的中文 msgid，如 "本次执行处理了 {n} 个文件"

        Returns:
            str | None: 格式化后的报告文本，文件数为 0 时返回 None
        """
        count = len(file_list)
        if count == 0:
            return None
        text = f"[cx.info]{_(msgid).format(n=count)}[/]"
        total = file_list.total_size
        if total.total_bytes > 0:
            text += f"（[cx.number]{total.pretty_string}[/]）"
        return text

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

        sort_mode = self.context.sort_mode
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
        """使用 MissionHQ 执行 Mission 列表。

        替换旧版的 MissionScheduler + DebugReporter + Progress 内联编排架构。
        MissionHQ 接管全部生命周期：中断（两段式）、进度（总+子）、debug 输出、文件追踪。

        Args:
            pretend: True = 模拟运行，False = 实际转码
        """
        ctx = self.context
        hq = MissionHQ(
            max_workers=ctx.max_workers,
            pretending=pretend,
            progress=self.progress,
            env=self.appenv,
            media_db=ctx.media_db,
        )
        # 订阅 HQ 总线事件
        hq.on(MISSION_STARTED, self._on_mission_started)
        hq.on(MISSION_RESULT, self._on_mission_result)
        hq.on(MISSION_FILE_LOGGED, self._on_file_logged)
        # 投喂 + 执行
        hq.add_missions(self.missions)
        hq.finish()
        results = run_async(hq.run())
        self._report_summary(results)

    def _on_mission_started(self, mission: Mission) -> None:
        """mission_started 事件处理：输出 WealthyDetailPanel。

        显示 Mission 的完整解析结果（仅在 -v/--debug 模式下可见）。
        面板位于进度条之前，方便 debug 时对照。

        Args:
            mission: 开始执行的 Mission
        """
        index = self.missions.index(mission)
        total = len(self.missions)
        short_id = str(mission.mission_id)[:6]
        self.appenv.whisper(
            WealthyDetailPanel(
                mission,
                title=(
                    f"[cx.debug]M[/] [cx.mk.badge]{short_id}[/] "
                    f"[{index + 1}/{total}] {mission.name}"
                ),
            )
        )

    def _on_mission_result(self, mission: Mission, result: MissionResult) -> None:
        """mission_result 事件处理：输出结果行。

        Args:
            mission: 已完成的 Mission
            result: 执行结果
        """
        self._report_mission_result(mission, result)

    def _on_file_logged(self, log_type: FileLogType, paths: list[Path]) -> None:
        """file_logged 事件处理：追踪文件的处理状态。

        根据事件类型将文件路径分发到 context 的相应文件列表中，
        在 stop() 阶段输出统计报告和清理 garbage。

        Args:
            log_type: 文件事件类型
            paths: 受影响的文件路径列表
        """
        if log_type == FileLogType.LOADED:
            for p in paths:
                self.context.processed_files.append(p)
        elif log_type == FileLogType.SAVED:
            for p in paths:
                self.context.generated_files.append(p)
        elif log_type == FileLogType.DEPRECATED:
            for p in paths:
                self.context.garbage_files.append(p)

    def _report_mission_result(self, mission: Mission, result: MissionResult) -> None:
        """输出单个 Mission 的结果文字行（旧版 make_line_report 风格）。

        格式：[M] [n→m] 任务名 ........ 状态（左对齐任务名 + 右对齐状态）

        Args:
            mission: 已完成的 Mission
            result: 执行结果
        """
        from rich.text import Text
        from rich.columns import Columns

        header = f"[cx.debug]M[/] [cx.whisper][{len(mission.inputs)}->{len(mission.outputs)}][/] "
        name_part = f"[cx.mk.mission.name]{mission.name}[/]"
        label = header + name_part

        if result == MissionResult.SUCCESS:
            right_str = f"[cx.mk.status.success]{_('完成')}[/]"
        elif result == MissionResult.FAILED:
            right_str = f"[cx.mk.status.failed]{_('运行异常')}[/]"
        elif result == MissionResult.CANCELED:
            right_str = f"[cx.mk.status.canceled]{_('被取消')}[/]"
        elif result == MissionResult.SKIPPED:
            right_str = f"[cx.whisper]{_('已跳过')}[/]"
        else:
            right_str = f"[cx.whisper]{result.value}[/]"

        left = Text.from_markup(label, justify="left", overflow="ellipsis")
        left.no_wrap = True
        right = Text.from_markup(right_str, justify="right")
        self.appenv.say(Columns([left, right], expand=True))

    def _report_summary(self, results: list[MissionResult]) -> None:
        """输出批量执行统计。

        Args:
            results: 所有 Mission 的执行结果
        """
        counts = Counter(results)

        if n := counts.get(MissionResult.SUCCESS, 0):
            self.appenv.say(_("成功执行 {n} 个任务。").format(n=n))
        if n := counts.get(MissionResult.FAILED, 0):
            self.appenv.say(_("{n} 个任务失败。").format(n=n))
        if n := counts.get(MissionResult.CANCELED, 0):
            self.appenv.say(_("{n} 个任务取消。").format(n=n))
        if n := counts.get(MissionResult.SKIPPED, 0):
            self.appenv.say(_("{n} 个任务跳过。").format(n=n))

    # --- 主流程 ---

    def run(self) -> None:
        ctx = self.context

        # 1. help / tutorial
        if ctx.show_help:
            help_component = MediaKillerHelp(self.appenv, self.context)
            help_component.show_help()
            return
        if ctx.show_full_help:
            help_component = MediaKillerHelp(self.appenv, self.context)
            help_component.show_full_help()
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
                    self.appenv.whisper(f"{p} {_('并非合法的文件名，不予处理。')}")
            for p in generated:
                self._open_in_editor(p)
            return

        # 3. 校验输入
        if not ctx.inputs:
            raise SafeError(_("未提供任何输入项，请使用 -h 查看帮助。"))

        # 4. 扫描输入项，区分 preset / source
        for raw in ctx.inputs:
            p = Path(raw)
            preset_path = self._resolve_preset(p)
            if preset_path is not None:
                try:
                    preset = PresetLoader().load(preset_path.resolve())
                except SafeError:
                    raise
                except Exception as e:
                    raise SafeError(
                        _("加载预设文件 {path} 失败: {err}").format(path=p, err=e)
                    )
                self.presets.append(preset)
                # 输出 Preset 详情面板（whisper，仅 --debug 可见）
                self.appenv.whisper(
                    WealthyDetailPanel(
                        preset,
                        title=f"{_('预设')} [cx.info]{preset.name}[/]",
                    )
                )
                self.appenv.whisper(
                    f"[cx.info]{_('配置文件路径')}[/] [cx.filepath]{p}[/]"
                )
            else:
                self.sources.append(p)
                self.appenv.whisper(
                    f"[cx.info]{_('媒体来源路径')}[/] [cx.filepath]{p}[/]"
                )

        if self.presets:
            self.appenv.say(
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
            self.appenv.say(f"{_('输出目录将被替换为:')} [cx.filepath]{output_dir}[/]")

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
            self.appenv.say(
                _("生成了 {count} 个任务。").format(count=len(current_missions))
            )

        # 8. continue 叠加
        all_missions = list(current_missions)
        if ctx.continue_mode:
            last = self._load_missions()
            self.appenv.say(
                _("从上次执行中恢复了 {count} 个任务……").format(count=len(last))
            )
            all_missions.extend(last)

        # 9. 排序去重
        self.missions = self._sort_and_dedup_missions(all_missions)

        if not self.missions:
            self.appenv.say(_("没有任务需要执行。"))
            return

        self.appenv.whisper(IndexedListPanel(self.missions, _("整理完的任务列表")))

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
            self.appenv.say(
                f"[cx.whisper]{_('检测到[cx.info]假装模式[/]，将不会真正执行任何操作。')}[/]"
            )
            self._execute_missions(pretend=True)
            return

        # 12. 实际转码
        self._execute_missions(pretend=False)
