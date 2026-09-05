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

# 配置文件缺省值：已完成条目保留 30 天
DEFAULT_RETENTION_DAYS = 30

# finish/pend/reset 动词 → 目标状态
_TRANSITION_STATUS = {
    "finish": EntryStatus.DONE,
    "pend": EntryStatus.PENDING,
    "reset": EntryStatus.TODO,
}

# 动词 → 人读确认文案
_TRANSITION_DONE_MESSAGE = {
    "finish": _("已完成"),
    "pend": _("已转入进行中"),
    "reset": _("已重置"),
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
        """执行应用主逻辑：帮助路由 + 标题行 + 逐动词分派。

        `-h`/`--tutorial` 在一切副作用之前路由（不触发配置初始化）；
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
        """add：登记一条内容到当前域。

        内容中字面 `\\n` 在此转换为真实换行（store 不处理）；
        空内容与缺失同义，一并报「缺少条目内容」。当前域（不含子域）
        已存在内容完全相同的条目时不重复写入，回执既有条目（`--json`
        幂等返回该条目对象）。
        """
        raw = self.context.argument
        if not raw or not raw.strip():
            raise SafeError(_("缺少条目内容"))
        content = raw.replace("\\n", "\n")
        existing = next(
            (e for e in store.domain_entries(current) if e.content == content), None
        )
        store.clean(current, retention)
        if existing is not None:
            if self.context.json_output:
                self._print_json(entry_to_json(existing))
            else:
                self.appenv.say(
                    r.Text(_("已存在相同内容的条目"), style="cx.info"),
                    r.Text(f"[{existing.id}]"),
                )
            return
        entry = store.add(current, content)
        if self.context.json_output:
            self._print_json(entry_to_json(entry))
        else:
            self.appenv.say(
                r.Text(_("已记录"), style="cx.info"), r.Text(f"[{entry.id}]")
            )

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

    def _do_transition(self, store: NoteStore, current: str, retention: int) -> None:
        """finish/pend/reset：解析目标条目并转移到对应状态。"""
        verb = self.context.verb
        entry = self._resolve_target(store, current)
        updated = store.transition(entry.id, _TRANSITION_STATUS[verb])
        assert updated is not None  # _resolve_target 保证存在
        store.clean(current, retention)
        if self.context.json_output:
            self._print_json(entry_to_json(updated))
        else:
            self.appenv.say(
                r.Text(_TRANSITION_DONE_MESSAGE[verb], style="cx.info"),
                r.Text(f"[{updated.id}]"),
            )

    def _do_erase(self, store: NoteStore, current: str, retention: int) -> None:
        """erase：解析目标条目并从存储中删除。"""
        entry = self._resolve_target(store, current)
        removed = store.erase(entry.id)
        assert removed is not None  # _resolve_target 保证存在
        store.clean(current, retention)
        if self.context.json_output:
            self._print_json(entry_to_json(removed))
        else:
            self.appenv.say(
                r.Text(_("已删除"), style="cx.info"), r.Text(f"[{removed.id}]")
            )

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

    # ── 目标解析 ──

    def _resolve_target(self, store: NoteStore, current: str) -> Entry:
        """把动词参数解析为唯一目标条目。

        匹配范围：ID 精确匹配为**全库**（ID 全局唯一）；文本子串匹配
        为**可见域**（当前域 + 下级域）。

        Args:
            store: 条目存储。
            current: 当前域字面。

        Returns:
            唯一命中的条目。

        Raises:
            SafeError: 参数缺失、无命中或命中多个（候选列表走 stderr）。
        """
        target = self.context.argument
        if not target or not target.strip():
            raise SafeError(_("缺少条目 ID 或文本片段"))
        entry = store.find_by_id(target)
        if entry is not None:
            return entry
        matches = store.find_by_text(current, target)
        if not matches:
            raise SafeError(_("未找到匹配的条目: {text}").format(text=target))
        if len(matches) > 1:
            lines = [
                _("匹配到多个条目，请改用 ID 或更精确的文本："),
                *[
                    f"[cx.note.hint]\\[{e.id}\\] {_content_preview(e)}[/]"
                    for e in matches
                ],
            ]
            raise SafeError("\n".join(lines))
        return matches[0]

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
