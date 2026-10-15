# Tasks

## 0. 存储层：工作集与显式落盘（cx_note/common/note_store.py）

- [x] 0.1 去掉 `add` / `transition` / `erase` / `clear_domain` / `clean` 内部全部 `_save()` 调用；`_save()` 收敛为公开 `flush() -> bool`（脏标记为真时按 tmp + `os.replace` 整文件重写，返回是否写盘），docstring 改为"一次运行至多落盘一次"
- [x] 0.2 语义对齐 take：`erase(eid)` → `take(eid)`、`clear_domain(domain)` → `take_domain(domain)`——只从工作集取走并返回被取走的条目（回显被删条目的依据），不落盘；保留现行 `clear_domain` 在域清空后弹出该域字面登记的簿记（`note_store.py:229-231`），`take_many` 走同一规则——"无条目的域不保留字面登记"这条不变式不因本次改造而变；`clean()` 整体移除（保留天数与作用域的判定移出存储层）
- [x] 0.3 新增 `set_content(eid, content) -> Entry | None`（`edit` 用；内容与原文相同时照样返回并计入本次变更条目，只是不置脏、不落盘）与 `take_many(entries) -> list[Entry]`（收尾清理用，按 id 取走）
- [x] 0.4 脏标记：只由"结果确有变化"的变更置位；`_load()` 后为假；docstring 写明"工作集与读盘结果一致时不写盘"
- [x] 0.5 `common/__init__.py` 导出面复核（`NoteStore` 成员变化不涉导出表；新增符号见 1.2）

## 1. 即将被清理的判据（cx_note/common/expiry.py，新增）

- [x] 1.1 `is_expiring(entry, scope, retention_days, now) -> bool`：终态（`done`/`dropped`）+ 终态打点非空 + `completed_at <= now - retention_days` + `is_within(entry.domain, scope)`；`retention_days <= 0` 恒为假
- [x] 1.2 `common/__init__.py` 导出 `is_expiring`；docstring 写明它是运行时派生判据（不固化进条目、不写入存储），消费方有三处、判据只有一份：呈现标记、`--json` 输出投影、收尾清理

## 2. 条目块与列表渲染（cx_note/components/list_view.py）

- [x] 2.1 `make_entry_block(entry, expiring=False) -> r.Table`：三列 = ID（`width=4`，逐字符着色徽章）/ 状态标号（自然宽）/ 内容（`ratio=1`）；`box=None`、`expand=True`、内容列显式 `overflow="fold"`（关掉 Rich 列默认的 ellipsis 截断）；终态弱化沿用（`dropped` → dim + strike，`done` → 徽章随行 dim）
- [x] 2.2 多行内容逐行呈现：先实测 `r.Markdown` 的硬换行（源行以两空格 + 换行连接，保留 `- ` 等 Markdown 解释）；实测不成立则退回保留真实换行的 `r.Text`。验收判据 = 三个源行输出三行（2.2 与 7.2 配套）
- [x] 2.3 删除 `_domain_table`（整域共享表随跨条目对齐一并消失）；`build_list_renderable` 改为"域标题行 + 逐条目块"
- [x] 2.4 `_rel_label` 修正：当前域子树之外的域改用绝对字面（现行实现假定域在当前域之下，子树外会切出乱码）——列表与回显共用（依赖方：3.4）
- [x] 2.5 `build_list_renderable` 增加两个参数：`expiring_ids: set[str]`（交给 2.6 判定标记）与"是否补齐当前域空块"（列表需要（指示所在位置）、回显不需要（无变更条目不打印））；调用点同步
- [x] 2.6 即将被清理的标记：`make_entry_block` 收 `expiring: bool`，为真时在首部标号之后追加词形「即将被清理」（样式名 `cx.note.expiring`，划入标号列、不新增列），为假时不占位

## 3. 应用层：阶段编排与回显（cx_note/application.py）

- [x] 3.1 `run()` 按四阶段显式编排：初始化（帮助路由 + 配置缺省，保持现状）→ 读盘（`NoteStore` + 本次运行共用的 `now`）→ 处理业务（动词分派）→ 收尾 `_finalize(store, current, retention, now)`
- [x] 3.2 `_finalize`：按 `is_expiring` 筛工作集 → `take_many` → 人读模式报告（确认行 + 被清条目的条目块，按域分块；作为**独立一段**落在业务输出之后）→ `store.flush()`；`--json` 模式不出清理报告。凡到达读盘的运行都会走到本方法（含 `clear` 拒绝确认这类无变更的正常结束）；异常路径不进入本方法（落盘随之不发生）
- [x] 3.3 动词改为只改工作集：去掉各动词里的 `store.clean(current, retention)`；`erase` / `clear` 改用 `take` / `take_domain`；`add` 的批内去重回执与 `transition` 的终态打点逻辑不动
- [x] 3.4 回显组装：本次变更条目按所属域分块（块间当前域子树居前、其余按 `canonical` 排序；块内按操作序），复用 2.x 的渲染；无变更条目不打印；`add` 的「已存在」回执条目计入变更条目
- [x] 3.5 确认行保留（条目级动词用「已〈结果〉 N 条：〈ID 列表〉」，ID 为裸 4 位 ID、空格分隔；`clear` 保留域级句式「已清空 N 条条目。」）；错误中止路径（无命中、多义、空参数）维持纯错误输出、不回显；`--json` 不回显
- [x] 3.6 application 侧用 `is_expiring` 算一次 `expiring_ids: set[str]`，供人读渲染（2.5 / 2.6 的参数）与 `--json` 输出投影（`{**entry_to_json(e), "expiring": True}`）共用；被取走的条目（`erase` / `clear` 的输出）不带该键；`common/entry.py` 不动

## 4. edit 动词

- [x] 4.1 `appcontext.py` 的 `VERBS` 表（argparse choices 与运行时分派共用的唯一来源）加入 `edit`；`app_help.py` 帮助分组与 `--tutorial` 教程补 `edit`（八动词 → 九动词）
- [x] 4.2 `application.py`：`edit` 分派——参数个数 MUST 恰为 2（不足或超出报 `SafeError` 中止，不修改任何条目）；第一参数走目标解析（**先给 `_resolve_targets` 加 `targets=None` 参数、缺省仍取 `context.arguments`**，`edit` 传 `self.context.arguments[:1]`——否则第二参数会被当成第二个目标，`application.py:339`）；第二参数做 `\n` → 真实换行转换；落 `store.set_content`；确认行「已修改 {count} 条：〈ID 列表〉」；计入本次变更条目，不改状态/域/ID/创建时间/终态打点，不做去重与撞车校验
- [x] 4.3 `--json`：走既有 `_print_json` 输出单元素条目数组

## 5. 候选清单与样式表

- [x] 5.1 删除 `application.py` 的 `_content_preview`（首行截断预览）；多义命中的候选改为条目块逐条呈现（复用 2.1）
- [x] 5.2 `appenv.py`：`cx.note.section` 由 `"bold"` 改为 `"bold yellow"`；新增 `cx.note.expiring`（建议 `"yellow"`）；删除全仓无引用的 `cx.note.id`

## 6. i18n 与文档归位

- [x] 6.1 新增 msgid：「即将被清理」、「已清理 {count} 条：」、「已修改 {count} 条：」、`edit` 参数个数错误文案
- [x] 6.2 依 `docs/agents/i18n.md` 的流程提取 / 更新 / 编译 `.po` 与 `.mo`（含 `en_US/LC_MESSAGES/cx-note.mo`），一并提交（domain `cx-note`）；MUST NOT 生成 `zh_CN` 的 `.po` / `.mo`（源语言即中文，空 msgstr 会覆盖 msgid）
- [x] 6.3 `help.md` 与 `help.en_US.md`：补 `edit` 用法，并修订"操作后回显"的描述（回显的是本次变更条目）
- [x] 6.4 根 `CONTEXT.md`：cx-note 的词条在 **`Domain：cxalio-studio-tools` 分区的术语表**里（仓库没有独立的 cxnote 分区）——收录新术语（条目块、即将被清理、变更条目）；改"清理"词条的执行时机（写操作附带 → 每次运行的收尾阶段）与作用域（该词条现写"仅限当前域"，与 spec 的"当前域及其下级域"不符，以 spec 为准）
- [x] 6.5 版本迭代（用户已拍板 **1.4.0**：minor）：旧值取 pyproject 现值 1.3.0 → 新号 **1.4.0** 写入 `cx_note/__init__.py` 的 `__version__`，pyproject 的 version 同步为 1.4.0（同一发布单元内其它未变更包的 `__version__` 不动）
- [x] 6.6 `uv run black .`

## 7. 验证（隔离 home 下的端到端实跑；仓库无测试基建）

- [x] 7.1 准备隔离环境：临时目录作 `USERPROFILE`（Windows 下 `ConfigManager` 走 `Path.home()`），在其中预置 `CxNote/notes.json`——裸 JSON 数组，条目对象形如 `{"id": "aaaa", "domain": "/a", "content": "…", "status": "done", "created_at": "2026-01-01T00:00:00", "completed_at": "2026-01-02T00:00:00"}`（`status` 取现行四态 token，`completed_at` 为 `null` 或 ISO 时刻）；用例数据含超长内容、多行内容（真实换行）、跨域条目、超龄终态条目（打点早于 `now - retention_days`）。**真实笔记库不得用于试探**
- [x] 7.2 条目块取证：`list` 输出中超长内容折行完整呈现且不出现省略号；多行内容输出为多行、每行与内容列对齐
- [x] 7.3 回显取证：状态流转、`add`（含「已存在」回执）、`erase`、跨域 ID 命中（域标题用绝对字面）；确认不再出现整域清单
- [x] 7.4 `edit` 取证：正常覆盖后状态与终态打点不变；参数个数为 1 / 3 时中止且磁盘无变化；改出与同域其它条目相同的内容
- [x] 7.5 即将被清理的标记与清理报告：`list` 中标出即将被清理的条目；只读运行的收尾仍清理并报告；`--json` 无清理报告且该条目带 `expiring` 键；`erase` / `clear` 的 `--json` 输出里被取走的条目 MUST NOT 带该键；`clear` 拒绝确认的运行照常执行清理并报告
- [x] 7.6 落盘语义：中途失败（无命中 / 多义）后存储文件内容与 `st_mtime_ns` 均不变；成功运行后 `st_mtime_ns` 变化且目录内不残留 `.tmp` 文件。"至多一次重写"在进程外不可直接计数，改为代码层核对——确认 `flush()` 的唯一调用点是 `_finalize`（静态核对调用点数量），连同实跑观察一并记入验证记录
- [x] 7.7 `--json` 契约回归：条目动词输出单元素数组、六键齐备、stdout 纯净（stdout 与 stderr 分开采集）
- [x] 7.8 清理临时产物：删除 `temp/` 下的探针脚本与临时 home 目录
