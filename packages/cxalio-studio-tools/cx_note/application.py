"""CxNote 应用入口。

`CxNoteApp` 实现 `IApplication` 接口，管理应用生命周期：
`start()` 注入 debug 模式 → `run()` 按动词分派业务 → `__exit__` 捕获
SafeError / KeyboardInterrupt 输出友好提示（错误走 stderr、exit 0，
与既有 5 工具一致；脚本消费者以 `--json` stdout 内容为准）。
"""

import json
import tomllib
from pathlib import Path
from typing import Any, override

from cx_note.components.list_view import build_list_renderable
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


def _content_preview(entry: Entry, limit: int = 60) -> str:
    """条目内容的首行截断预览（定位歧义的候选列表用）。"""
    first_line = entry.content.splitlines()[0] if entry.content else ""
    return first_line[:limit] + "…" if len(first_line) > limit else first_line


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
        """退出应用。始终执行 stop()，捕获已知异常类型输出友好提示。"""
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is not None and issubclass(exc_type, SafeError):
            self.appenv.say(f"[{exc_val.style}]{exc_val}[/]")
            result = True
        elif exc_type is KeyboardInterrupt:
            self.appenv.say(f"[cx.warning]{_('用户中断')}[/]")
            result = True
        return result

    # ── 入口 ──

    @override
    def run(self) -> None:
        """执行应用主逻辑：帮助路由 + 空参数拦截 + 标题行 + 逐动词分派。

        `-h`/`--tutorial` 在一切副作用之前路由（不触发配置初始化）；
        空参数（strip 后为空的元素）一律报 SafeError 中止；
        `--json` 时跳过标题行与一切 say 装饰，成功路径零 say，
        stdout 仅有 JSON（内置 print，防 Rich 折行破坏长行）。
        """
        ctx = self.context
        json_out = ctx.json_output
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
        if not json_out:
            self.appenv.say(f"[cx.info]cxnote[/] [cx.number]v{__version__}[/]")
        if not self._config_file().exists():
            self._write_retention(DEFAULT_RETENTION_DAYS)

        current = resolve_domain(Path.cwd(), ctx.domain_param, ctx.global_flag)
        store = NoteStore(ConfigManager("CxNote").get_file("notes.json"))
        retention = self._read_retention()

        if ctx.verb == "add":
            self._do_add(store, current, retention)
        elif ctx.verb == "list":
            self._do_list(store, current)
        elif ctx.verb in _TRANSITION_STATUS:
            self._do_transition(store, current, retention)
        elif ctx.verb == "erase":
            self._do_erase(store, current, retention)
        elif ctx.verb == "clear":
            self._do_clear_domain(store, current, retention)

    # ── 动词实现 ──

    def _do_add(self, store: NoteStore, current: str, retention: int) -> None:
        """add：按参数序逐条登记内容到当前域（批量）。

        每个参数独立做 `\\n` → 换行转换；「已存在」判定基于当前存储
        加本批已建条目（`add 牛奶 牛奶` → 第 1 个新建、第 2 个命中
        已存在）。未提供参数报「缺少条目内容」。结果分「新建」「已存在」
        两组分别打印确认行；JSON 数组按参数序。
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
        store.clean(current, retention)
        # 参数序：遍历 raws，每条从 existing_seen 取对应条目
        all_results = [existing_seen[r.replace("\\n", "\n")] for r in raws]
        if self.context.json_output:
            self._print_json([entry_to_json(e) for e in all_results])
        else:
            if new_entries:
                ids = " ".join(f"[{e.id}]" for e in new_entries)
                self.appenv.say(
                    r.Text(
                        _("已记录 {count} 条：").format(count=len(new_entries)),
                        style="cx.info",
                    ),
                    r.Text(ids),
                )
            if dup_entries:
                ids = " ".join(f"[{e.id}]" for e in dup_entries)
                self.appenv.say(
                    r.Text(
                        _("已存在 {count} 条：").format(count=len(dup_entries)),
                        style="cx.info",
                    ),
                    r.Text(ids),
                )
            self._echo_list(store, current)

    def _do_list(self, store: NoteStore, current: str) -> None:
        """list：按域分组显示可见域条目。

        分组：当前域组在前，其余按身份键（canonical）排序；组内按
        创建时间升序。`--json` 默认只含当前域组条目；加 `--full` 后
        含全部下级域，顺序与人读一致（不保留树状分组）。

        Args:
            store: 条目存储。
            current: 当前域字面。
        """
        groups = self._group_for_list(store.visible_entries(current), current)
        if self.context.json_output:
            current_key = canonical(current)
            scope = (
                groups
                if self.context.full
                else [(d, es) for d, es in groups if canonical(d) == current_key]
            )
            self._print_json(
                [entry_to_json(e) for _, entries in scope for e in entries]
            )
            return
        if not groups:
            self.appenv.say(_("当前域暂无条目"))
            return
        self.appenv.say(build_list_renderable(groups, current, self.context.full))

    def _echo_list(self, store: NoteStore, current: str) -> None:
        """操作后回显：确认行之下打印当前域直属条目列表。

        人读模式下所有动词操作成功后调用；`--json` 直接返回，输出契约
        不变。当前域无直属条目时打印空态文案；有条目时复用 list 的单域
        块渲染（标题行 + 三列小表），只含当前域，不含下级域。

        Args:
            store: 条目存储。
            current: 当前域字面。
        """
        if self.context.json_output:
            return
        entries = store.domain_entries(current)
        if not entries:
            self.appenv.say(_("当前域暂无条目"))
            return
        self.appenv.say(build_list_renderable([(current, entries)], current, False))

    def _do_transition(self, store: NoteStore, current: str, retention: int) -> None:
        """finish/pend/reset/drop：批量解析目标条目并转移到对应状态。

        原子式：全部解析成功后逐个执行转移；JSON 数组按参数序。
        """
        verb = self.context.verb
        targets = self._resolve_targets(store, current)
        status = _TRANSITION_STATUS[verb]
        updated_list: list[Entry] = []
        for target in targets:
            updated = store.transition(target.id, status)
            assert updated is not None  # _resolve_targets 保证存在
            updated_list.append(updated)
        store.clean(current, retention)
        if self.context.json_output:
            self._print_json([entry_to_json(u) for u in updated_list])
        else:
            msg = _TRANSITION_DONE_MESSAGE[verb]
            self._print_batch_confirm(msg, targets)
            self._echo_list(store, current)

    def _do_erase(self, store: NoteStore, current: str, retention: int) -> None:
        """erase：批量解析目标条目并从存储中删除。

        原子式：全部解析成功后逐个删除；JSON 数组按参数序。
        """
        targets = self._resolve_targets(store, current)
        removed_list: list[Entry] = []
        for target in targets:
            removed = store.erase(target.id)
            assert removed is not None  # _resolve_targets 保证存在
            removed_list.append(removed)
        store.clean(current, retention)
        if self.context.json_output:
            self._print_json([entry_to_json(e) for e in removed_list])
        else:
            self._print_batch_confirm(_("已删除 {count} 条："), targets)
            self._echo_list(store, current)

    def _do_clear_domain(self, store: NoteStore, current: str, retention: int) -> None:
        """clear：清空当前工作域直属条目（不含子域）。

        人读模式先报告目标域与条目数、经确认（y）后执行；`--json`
        跳过确认直接执行并输出被清条目数组。空域不确认、直接回执。
        """
        doomed = store.domain_entries(current)
        if self.context.json_output:
            removed = store.clear_domain(current)
            store.clean(current, retention)
            self._print_json([entry_to_json(e) for e in removed])
            return
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
        removed = store.clear_domain(current)
        store.clean(current, retention)
        self.appenv.say(
            r.Text(_("已清空 {n} 条条目。").format(n=len(removed)), style="cx.info")
        )
        self._echo_list(store, current)

    # ── 目标解析 ──

    def _resolve_targets(self, store: NoteStore, current: str) -> list[Entry]:
        """批量解析参数列表为目标条目集合（按 id 去重，保留首次出现）。

        逐个参数解析（ID 全库精确 → 文本限可见域），无命中或多义
        记入问题清单；全部解析完再判断，有问题则一次 SafeError 汇总
        列出每一项，确保一条不动。重复目标参数（如 `finish abc abc`）
        只处理首次出现的那一条，确认行与 JSON 数组均只反映实际处理
        的条目。

        Args:
            store: 条目存储。
            current: 当前域字面。

        Returns:
            按去重后参数序排列的目标条目列表（不重复）。

        Raises:
            SafeError: 缺少参数、任一参数无命中或多义。
        """
        args = self.context.arguments
        if not args:
            raise SafeError(_("缺少条目 ID 或文本片段"))
        results: list[Entry] = []
        seen_ids: set[str] = set()
        problems: list[str] = []
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
                candidates = ", ".join(
                    f"[{e.id}] {_content_preview(e)}" for e in matches
                )
                problems.append(
                    _("第 {n} 个参数（{text}）：匹配到多个条目——{candidates}").format(
                        n=i, text=target, candidates=candidates
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
            raise SafeError("\n".join(lines))
        return results

    def _print_batch_confirm(self, template: str, entries: list[Entry]) -> None:
        """打印批量操作的单行确认：已完成 N 条：[ids]。

        Args:
            template: 完整确认文案模板（含 ``{count}`` 占位符）。
            entries: 本次操作涉及的条目列表。
        """
        if not entries:
            return
        ids = " ".join(f"[{e.id}]" for e in entries)
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
