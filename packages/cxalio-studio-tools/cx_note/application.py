"""CxNote 应用入口。

`CxNoteApp` 实现 `IApplication` 接口，管理应用生命周期：
`start()` 注入 debug 模式 → `run()` 四阶段执行（初始化 → 读盘 →
处理业务 → 收尾）→ `__exit__` 捕获 SafeError / KeyboardInterrupt
输出友好提示（错误走 stderr、exit 0，与既有 5 工具一致；脚本消费者
以 `--json` stdout 内容为准）。

运行模型：动词只改内存工作集并产出输出；超龄清理与落盘收归收尾
阶段（`_finalize`），一次运行至多原子重写存储一次。异常路径从
`run()` 抛出、不再进入收尾，条目存储文件保持运行前内容。
"""

import json
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any, override

from cx_note.components.list_view import build_list_renderable, make_entry_block
from cx_note.i18n import _
from cx_tools.app import ConfigManager, IAppEnvironment, IApplication, SafeError
from cx_wealthy import rich_types as r

from . import __version__
from .app_help import CxNoteHelp
from .appcontext import CxNoteContext
from .common import (
    Entry,
    EntryStatus,
    NoteStore,
    canonical,
    entry_to_json,
    is_expiring,
    is_within,
    resolve_domain,
)

# 配置文件缺省值：终态条目保留 30 天（终态 = 已完成/已取消）
DEFAULT_RETENTION_DAYS = 30

# finish/pend/reset/drop 动词 → 目标状态
_TRANSITION_STATUS = {
    "finish": EntryStatus.DONE,
    "pend": EntryStatus.PENDING,
    "reset": EntryStatus.TODO,
    "drop": EntryStatus.DROPPED,
}

# 动词 → 人读确认文案（完整模板，含 {count} 占位符）
_TRANSITION_DONE_MESSAGE: dict[str, str] = {
    "finish": _("已完成 {count} 条："),
    "pend": _("已转入进行中 {count} 条："),
    "reset": _("已重置 {count} 条："),
    "drop": _("已取消 {count} 条："),
}


class _RenderableSafeError(SafeError):
    """携带条目块渲染体的 SafeError（定位多义时先呈现候选再报摘要）。

    `SafeError` 只携带字符串，`__exit__` 又会把消息包进样式标记；
    错误路径上要渲染条目块，走本子类：`CxNoteApp.__exit__` 捕获到它
    时先 `say()` 渲染体，再呈现带样式的错误文本。框架 `cx-tools` 不动。

    Args:
        message: 错误摘要文本。
        renderable: 随错误一同呈现的渲染体（候选条目块等）。
    """

    def __init__(self, message: str, renderable: r.RenderableType) -> None:
        super().__init__(message)
        self.renderable = renderable


class CxNoteApp(IApplication):
    """CxNote 主应用。

    Args:
        appenv: 应用环境实例。
        context: 命令行上下文。
    """

    def __init__(
        self,
        appenv: IAppEnvironment,
        context: CxNoteContext,
    ):
        super().__init__(appenv, context)
        self.context = context
        # 本次运行的共享上下文：run() 读盘阶段覆盖——保留天数与基准
        # 时刻（now 只取一次，整 run 共用，超龄判定与呈现必然一致）。
        self._run_retention: int = DEFAULT_RETENTION_DAYS
        self._run_now: datetime = datetime.min

    @override
    def start(self) -> None:
        """启动应用：注入 debug 模式。"""
        self.appenv.set_debug_mode(self.context.debug_mode)

    @override
    def stop(self) -> None:
        """停止应用。无工具特定清理。"""
        pass

    @override
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出应用。始终执行 stop()，捕获已知异常类型输出友好提示。

        携带渲染体的 SafeError（`_RenderableSafeError`，如定位多义的
        候选条目块）先打印渲染体，再呈现带样式的错误摘要。
        """
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is not None and issubclass(exc_type, SafeError):
            if isinstance(exc_val, _RenderableSafeError):
                self.appenv.say(exc_val.renderable)
            self.appenv.say(f"[{exc_val.style}]{exc_val}[/]")
            result = True
        elif exc_type is KeyboardInterrupt:
            self.appenv.say(f"[cx.warning]{_('用户中断')}[/]")
            result = True
        return result

    # ── 入口 ──

    @override
    def run(self) -> None:
        """执行应用主逻辑：初始化 → 读盘 → 处理业务 → 收尾 四阶段。

        初始化：`-h`/`--tutorial` 在一切副作用之前路由（不触发配置
        初始化）；空参数（strip 后为空的元素）一律报 SafeError 中止；
        标题行与配置缺省初始化。读盘：解析当前域、构造 `NoteStore`
        （损坏即抛）、读保留天数、取本次运行共用的基准时刻 `now`。
        处理业务：动词只改内存工作集并输出（人读确认行 + 变更条目
        回显；`--json` 跳过标题行与一切 say 装饰，成功路径零 say，
        stdout 仅有 JSON——内置 print，防 Rich 折行破坏长行）。收尾：
        `_finalize` 执行超龄清理并落盘——凡到达读盘的运行都会走到；
        异常从 run() 抛出、不再进入收尾，存储文件保持原状。
        """
        ctx = self.context
        # ── 初始化 ──
        if ctx.show_help:
            CxNoteHelp(self.appenv, ctx).show_help()
            return
        if ctx.show_full_help:
            CxNoteHelp(self.appenv, ctx).show_full_help()
            return
        # 空参数检查——任何动词显式收到空参数（strip 后为空）即报错中止；
        # 未提供参数（默认空列表）不受影响。
        empty_problems = [
            (i, raw) for i, raw in enumerate(ctx.arguments, 1) if not raw.strip()
        ]
        if empty_problems:
            lines = [
                _("参数中包含空内容："),
                *[
                    _("第 {n} 个参数（{raw!r}）").format(n=n, raw=raw)
                    for n, raw in empty_problems
                ],
            ]
            raise SafeError("\n".join(lines))
        if not ctx.json_output:
            self.appenv.say(f"[cx.info]cxnote[/] [cx.number]v{__version__}[/]")
        if not self._config_file().exists():
            self._write_retention(DEFAULT_RETENTION_DAYS)
        # ── 读盘 ──
        current = resolve_domain(Path.cwd(), ctx.domain_param, ctx.global_flag)
        store = NoteStore(ConfigManager("CxNote").get_file("notes.json"))
        retention = self._read_retention()
        self._run_retention = retention
        self._run_now = datetime.now()
        # ── 处理业务 ──
        if ctx.verb == "add":
            self._do_add(store, current)
        elif ctx.verb == "list":
            self._do_list(store, current)
        elif ctx.verb == "edit":
            self._do_edit(store, current)
        elif ctx.verb in _TRANSITION_STATUS:
            self._do_transition(store, current)
        elif ctx.verb == "erase":
            self._do_erase(store, current)
        elif ctx.verb == "clear":
            self._do_clear(store, current)
        # ── 收尾 ──
        self._finalize(store, current, retention, self._run_now)

    # ── 动词实现 ──

    def _do_add(self, store: NoteStore, current: str) -> None:
        """add：按参数序逐条登记内容到当前域（批量）。

        每个参数独立做 `\\n` → 换行转换；「已存在」判定基于当前存储
        加本批已建条目（`add 牛奶 牛奶` → 第 1 个新建、第 2 个命中
        已存在）。未提供参数报「缺少条目内容」。结果分「新建」「已存在」
        两组分别打印确认行；本次变更条目 = 新建条目 + 去重回执条目，
        按参数序回显；JSON 数组按参数序（即将被清理的条目带 `expiring` 键）。
        """
        raws = self.context.arguments
        if not raws:
            raise SafeError(_("缺少条目内容"))
        existing_seen: dict[str, Entry] = {
            e.content: e for e in store.domain_entries(current)
        }
        new_entries: list[Entry] = []
        dup_entries: list[Entry] = []
        for raw in raws:
            content = raw.replace("\\n", "\n")
            hit = existing_seen.get(content)
            if hit is not None:
                dup_entries.append(hit)
            else:
                entry = store.add(current, content)
                existing_seen[content] = entry
                new_entries.append(entry)
        # 参数序：遍历 raws，每条从 existing_seen 取对应条目
        changed = [existing_seen[r.replace("\\n", "\n")] for r in raws]
        expiring_ids = self._expiring_ids(store, current)
        if self.context.json_output:
            self._print_json([self._project_json(e, expiring_ids) for e in changed])
            return
        if new_entries:
            ids = " ".join(e.id for e in new_entries)
            template = _("已记录 {count} 条：")
            self.appenv.say(
                r.Text(template.format(count=len(new_entries)), style="cx.info"),
                r.Text(ids),
            )
        if dup_entries:
            ids = " ".join(e.id for e in dup_entries)
            template = _("已存在 {count} 条：")
            self.appenv.say(
                r.Text(template.format(count=len(dup_entries)), style="cx.info"),
                r.Text(ids),
            )
        self._echo_changed(changed, current, expiring_ids)

    def _do_list(self, store: NoteStore, current: str) -> None:
        """list：按域分组显示可见域条目。

        分组：当前域组在前，其余按身份键（canonical）排序；组内按
        创建时间升序。`--json` 默认只含当前域组条目；加 `--full` 后
        含全部下级域，顺序与人读一致（不保留树状分组）。仍在工作集
        中且即将被清理的条目：人读带词形标记，JSON 带 `expiring` 键。

        Args:
            store: 条目存储。
            current: 当前域字面。
        """
        groups = self._group_for_list(store.visible_entries(current), current)
        expiring_ids = self._expiring_ids(store, current)
        if self.context.json_output:
            current_key = canonical(current)
            scope = (
                groups
                if self.context.full
                else [(d, es) for d, es in groups if canonical(d) == current_key]
            )
            self._print_json(
                [
                    self._project_json(e, expiring_ids)
                    for _, entries in scope
                    for e in entries
                ]
            )
            return
        if not groups:
            self.appenv.say(_("当前域暂无条目"))
            return
        self.appenv.say(
            build_list_renderable(
                groups, current, self.context.full, expiring_ids=expiring_ids
            )
        )

    def _do_transition(self, store: NoteStore, current: str) -> None:
        """finish/pend/reset/drop：批量解析目标条目并转移到对应状态。

        原子式：全部解析成功后逐个执行转移；JSON 数组按参数序。
        确认行 + 转移后条目（按所属域分块）回显。
        """
        verb = self.context.verb
        targets = self._resolve_targets(store, current)
        status = _TRANSITION_STATUS[verb]
        updated_list: list[Entry] = []
        for target in targets:
            updated = store.transition(target.id, status)
            assert updated is not None  # _resolve_targets 保证存在
            updated_list.append(updated)
        expiring_ids = self._expiring_ids(store, current)
        if self.context.json_output:
            self._print_json(
                [self._project_json(u, expiring_ids) for u in updated_list]
            )
            return
        msg = _TRANSITION_DONE_MESSAGE[verb]
        self._print_batch_confirm(msg, targets)
        self._echo_changed(updated_list, current, expiring_ids)

    def _do_edit(self, store: NoteStore, current: str) -> None:
        """edit：以 `TARGET CONTENT` 两参数覆盖单条条目的内容。

        第一参数按目标定位规则解析单条条目；第二参数为新内容，字面
        `\\n` → 真实换行（与 `add` 一致）。参数个数不是 2 时报错中止、
        一条不动。覆盖只改内容文本——状态、所属域、ID、创建时间与
        终态打点均不变；不做去重或撞车校验，新内容与原文相同也照常
        按一次变更处理（工作集与读盘结果一致时收尾不落盘）。确认行 +
        覆盖后条目回显；`--json` 输出单元素条目数组。

        Args:
            store: 条目存储。
            current: 当前域字面。

        Raises:
            SafeError: 参数个数不是 2，或目标参数解析失败。
        """
        args = self.context.arguments
        if len(args) != 2:
            raise SafeError(_("edit 需要恰好两个参数（目标与新内容）"))
        target = self._resolve_targets(store, current, targets=args[:1])[0]
        updated = store.set_content(target.id, args[1].replace("\\n", "\n"))
        assert updated is not None  # _resolve_targets 保证存在
        expiring_ids = self._expiring_ids(store, current)
        if self.context.json_output:
            self._print_json([self._project_json(updated, expiring_ids)])
            return
        self._print_batch_confirm(_("已修改 {count} 条："), [updated])
        self._echo_changed([updated], current, expiring_ids)

    def _do_erase(self, store: NoteStore, current: str) -> None:
        """erase：批量解析目标条目并从工作集取走。

        原子式：全部解析成功后逐个取走（`store.take`）；JSON 数组按
        参数序，被取走的条目不再携带 `expiring` 键（收尾不会再清它们）。
        确认行 + 被取走条目（按取走前状态、所属域分块）回显。
        """
        targets = self._resolve_targets(store, current)
        removed_list: list[Entry] = []
        for target in targets:
            removed = store.take(target.id)
            assert removed is not None  # _resolve_targets 保证存在
            removed_list.append(removed)
        if self.context.json_output:
            self._print_json([entry_to_json(e) for e in removed_list])
            return
        self._print_batch_confirm(_("已删除 {count} 条："), removed_list)
        self._echo_changed(removed_list, current, frozenset(), taken=True)

    def _do_clear(self, store: NoteStore, current: str) -> None:
        """clear：清空当前工作域直属条目（不含子域）。

        人读模式先报告目标域与条目数、经确认（y）后执行（`store.take_domain`）；
        `--json` 跳过确认直接执行并输出被清条目数组（不带 `expiring`
        键）。空域不确认、直接回执；拒绝确认不改工作集，但运行照常
        走到收尾（超龄清理与落盘不受影响）。
        """
        if self.context.json_output:
            removed = store.take_domain(current)
            self._print_json([entry_to_json(e) for e in removed])
            return
        doomed = store.domain_entries(current)
        if not doomed:
            self.appenv.say(_("当前域没有条目"))
            return
        self.appenv.say(
            _("将清空域 {domain} 的 {n} 条条目（不含子域，不可恢复）。").format(
                domain=current, n=len(doomed)
            )
        )
        answer = self.appenv.console.input(_("确认清空？[y/N] "))
        if answer.strip().lower() != "y":
            self.appenv.say(_("已取消"))
            return
        removed = store.take_domain(current)
        template = _("已清空 {n} 条条目。")
        self.appenv.say(r.Text(template.format(n=len(removed)), style="cx.info"))
        self._echo_changed(removed, current, frozenset(), taken=True)

    # ── 收尾 ──

    def _finalize(
        self, store: NoteStore, current: str, retention: int, now: datetime
    ) -> None:
        """收尾：超龄清理 + 报告 + 唯一落盘点。

        凡到达读盘的运行都会走到本方法（含无变更的正常结束，如
        `clear` 拒绝确认）；异常路径从 `run()` 抛出、不再进入本方法，
        条目存储文件保持运行前内容。清理按统一判据（`is_expiring`）
        筛选当前工作集并 `take_many` 取走；人读模式在实际清除了条目
        时打印独立于业务输出的报告（确认行 + 被清条目的条目块，按所
        属域分块，条目块按消亡样式呈现）；`--json` 模式不出清理报告。末尾的显式落盘调用
        是全工具唯一的写盘点：工作集与读盘结果一致时不写盘。

        Args:
            store: 条目存储（本次运行的工作集）。
            current: 当前域字面（清理作用域，含下级域）。
            retention: 终态条目保留天数。
            now: 本次运行的基准时刻。
        """
        doomed = [e for e in store.entries() if is_expiring(e, current, retention, now)]
        taken = store.take_many(doomed)
        if taken and not self.context.json_output:
            ids = " ".join(e.id for e in taken)
            template = _("已清理 {count} 条：")
            self.appenv.say(
                r.Text(template.format(count=len(taken)), style="cx.info"),
                r.Text(ids),
            )
            groups = self._group_changed(taken, current)
            self.appenv.say(
                build_list_renderable(
                    groups, current, False, fill_current_empty=False, taken=True
                )
            )
        store.flush()

    # ── 回显与投影 ──

    def _echo_changed(
        self,
        changed: list[Entry],
        current: str,
        expiring_ids: frozenset[str],
        taken: bool = False,
    ) -> None:
        """确认行之下回显本次变更条目：按所属域分块的条目块。

        人读模式专用；无变更条目时整段不打印（确认行已述结果）。
        块间当前域子树居前、其余按域身份键排序，块内按操作序；不注入
        空的当前域块（回显语义）。

        Args:
            changed: 本次变更条目（操作序）。
            current: 当前域字面。
            expiring_ids: 即将被清理的条目 ID 集合（块内标记用）。
            taken: 变更条目是否已被取走（erase/clear 路径）——透传给
                渲染层按消亡样式呈现；转移/edit/add 路径保持默认。
        """
        if not changed:
            return
        groups = self._group_changed(changed, current)
        self.appenv.say(
            build_list_renderable(
                groups,
                current,
                False,
                expiring_ids=expiring_ids,
                fill_current_empty=False,
                taken=taken,
            )
        )

    def _expiring_ids(self, store: NoteStore, current: str) -> frozenset[str]:
        """计算当前工作集中即将被清理的条目 ID 集合。

        判据唯一（`is_expiring`），基准时刻与保留天数取本次运行的共
        享值；人读标记与 `--json` 输出投影共用本集合，收尾清理按同一
        判据重筛工作集。

        Args:
            store: 条目存储。
            current: 当前域字面（作用域，含下级域）。

        Returns:
            即将被清理的条目 ID 集合。
        """
        return frozenset(
            e.id
            for e in store.entries()
            if is_expiring(e, current, self._run_retention, self._run_now)
        )

    @staticmethod
    def _project_json(entry: Entry, expiring_ids: frozenset[str]) -> dict[str, Any]:
        """JSON 输出投影：仍在工作集中且即将被清理的条目附加 `expiring` 键。

        被取走的条目（`erase` / `clear` 的输出）不经本投影——收尾不再
        清除它们，MUST NOT 携带该键。

        Args:
            entry: 待输出的条目。
            expiring_ids: 即将被清理的条目 ID 集合。

        Returns:
            六键齐备的条目对象；即将被清理时另带 `expiring: True`。
        """
        if entry.id in expiring_ids:
            return {**entry_to_json(entry), "expiring": True}
        return entry_to_json(entry)

    # ── 目标解析 ──

    def _resolve_targets(
        self, store: NoteStore, current: str, targets: list[str] | None = None
    ) -> list[Entry]:
        """批量解析参数列表为目标条目集合（按 id 去重，保留首次出现）。

        逐个参数解析（ID 全库精确 → 文本限可见域），无命中或多义
        记入问题清单；全部解析完再判断，有问题则一次 SafeError 汇总
        列出每一项，确保一条不动。多义候选逐条以条目块呈现（随
        `_RenderableSafeError` 先于错误摘要打印）。重复目标参数（如
        `finish abc abc`）只处理首次出现的那一条，确认行与 JSON 数组
        均只反映实际处理的条目。

        Args:
            store: 条目存储。
            current: 当前域字面。
            targets: 待解析的参数列表；None 时取 `context.arguments`
                （`edit` 传首参数单元素列表，避免新内容被当成第二个目标）。

        Returns:
            按去重后参数序排列的目标条目列表（不重复）。

        Raises:
            SafeError: 缺少参数、任一参数无命中或多义。
        """
        args = self.context.arguments if targets is None else targets
        if not args:
            raise SafeError(_("缺少条目 ID 或文本片段"))
        results: list[Entry] = []
        seen_ids: set[str] = set()
        problems: list[str] = []
        candidate_sections: list[r.RenderableType] = []
        expiring_ids: frozenset[str] | None = None
        for i, target in enumerate(args, 1):
            entry = store.find_by_id(target)
            if entry is not None:
                if entry.id not in seen_ids:
                    seen_ids.add(entry.id)
                    results.append(entry)
                continue
            matches = store.find_by_text(current, target)
            if not matches:
                problems.append(
                    _("第 {n} 个参数（{text}）：未找到匹配的条目").format(
                        n=i, text=target
                    )
                )
            elif len(matches) > 1:
                if expiring_ids is None:
                    expiring_ids = self._expiring_ids(store, current)
                heading = _("第 {n} 个参数（{text}）的候选：").format(n=i, text=target)
                candidate_sections.append(
                    r.Group(
                        r.Text(heading),
                        *(
                            make_entry_block(e, expiring=e.id in expiring_ids)
                            for e in matches
                        ),
                    )
                )
                problems.append(
                    _("第 {n} 个参数（{text}）：匹配到多个条目").format(
                        n=i, text=target
                    )
                )
            else:
                matched = matches[0]
                if matched.id not in seen_ids:
                    seen_ids.add(matched.id)
                    results.append(matched)
        if problems:
            lines = [
                _("以下参数解析失败："),
                *problems,
            ]
            if candidate_sections:
                raise _RenderableSafeError(
                    "\n".join(lines), r.Group(*candidate_sections)
                )
            raise SafeError("\n".join(lines))
        return results

    def _print_batch_confirm(self, template: str, entries: list[Entry]) -> None:
        """打印批量操作的单行确认：已〈结果〉 N 条：〈裸 4 位 ID 空格分隔〉。

        Args:
            template: 完整确认文案模板（含 ``{count}`` 占位符）。
            entries: 本次操作涉及的条目列表；为空时不打印。
        """
        if not entries:
            return
        ids = " ".join(e.id for e in entries)
        self.appenv.say(
            r.Text(
                template.format(count=len(entries)),
                style="cx.info",
            ),
            r.Text(ids),
        )

    # ── 分组与配置 ──

    @staticmethod
    def _group_for_list(
        visible: list[Entry], current: str
    ) -> list[tuple[str, list[Entry]]]:
        """把可见条目按域归组：当前域组在前，其余按身份键排序。

        组键取 canonical（大小写不敏感合并），显示字面取组内首见；
        组内按创建时间升序（旧→新）。

        Args:
            visible: 当前域及其下级域的条目（插入序）。
            current: 当前域字面。

        Returns:
            `(域字面, 条目列表)` 序列。
        """
        buckets: dict[str, list[Entry]] = {}
        literals: dict[str, str] = {}
        for entry in visible:
            key = canonical(entry.domain)
            buckets.setdefault(key, []).append(entry)
            literals.setdefault(key, entry.domain)
        current_key = canonical(current)
        ordered = sorted(buckets, key=lambda k: (k != current_key, k))
        return [
            (
                literals[key],
                sorted(buckets[key], key=lambda e: e.created_at),
            )
            for key in ordered
        ]

    @staticmethod
    def _group_changed(
        changed: list[Entry], current: str
    ) -> list[tuple[str, list[Entry]]]:
        """把本次变更条目按所属域归组：当前域子树居前，其余按身份键排序。

        与 `_group_for_list` 的区别：块内保持本次操作的处理顺序（不按
        创建时间重排——回显块序与确认行 ID 列表对应）；域可落在当前域
        子树之外（跨域 ID 命中，渲染时以绝对字面作标题）。组键取
        canonical（大小写不敏感合并），显示字面取组内首见。

        Args:
            changed: 本次变更条目（操作序）。
            current: 当前域字面。

        Returns:
            `(域字面, 条目列表)` 序列。
        """
        buckets: dict[str, list[Entry]] = {}
        literals: dict[str, str] = {}
        for entry in changed:
            key = canonical(entry.domain)
            buckets.setdefault(key, []).append(entry)
            literals.setdefault(key, entry.domain)
        ordered = sorted(
            buckets, key=lambda k: (not is_within(literals[k], current), k)
        )
        return [(literals[key], buckets[key]) for key in ordered]

    @staticmethod
    def _config_file() -> Path:
        """config.toml 路径（纯路径拼接，不创建）。"""
        return ConfigManager("CxNote").get_file("config.toml")

    @staticmethod
    def _read_retention() -> int:
        """读取保留天数配置；文件不存在或无键时返回缺省值。

        Returns:
            `retention_days` 整数值。

        Raises:
            SafeError: 配置文件损坏或 `retention_days` 非整数。
        """
        path = CxNoteApp._config_file()
        broken = _("配置文件已损坏: {path}").format(path=path)
        if not path.exists():
            return DEFAULT_RETENTION_DAYS
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError) as e:
            raise SafeError(broken) from e
        value = data.get("retention_days", DEFAULT_RETENTION_DAYS)
        if not isinstance(value, int) or isinstance(value, bool):
            raise SafeError(broken)
        return value

    @staticmethod
    def _write_retention(value: int) -> None:
        """写入保留天数（单键 TOML 手写，不引入 tomli_w）。"""
        path = CxNoteApp._config_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"retention_days = {value}\n", encoding="utf-8")

    @staticmethod
    def _print_json(payload: Any) -> None:
        """向 stdout 输出纯净 JSON。

        用内置 `print` 而非 Rich Console——Console 默认 soft_wrap=False
        会把长行折行，破坏 JSON 行结构。
        """
        print(json.dumps(payload, ensure_ascii=False, indent=2))
