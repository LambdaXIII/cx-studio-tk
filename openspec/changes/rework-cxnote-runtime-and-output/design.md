# Design

## Context

动机见 proposal.md（Why）。现状与约束：

- cxnote 现行分层：`common/`（`domain.py` 域解析、`entry.py` 条目模型、`note_store.py` 单 JSON 存储——均为不依赖 appenv 的纯逻辑，经 `common/__init__.py` 汇聚导出）、`components/list_view.py`（纯函数渲染层，返回 renderable 由 application 用 `appenv.say()` 打印）、`application.py`（`CxNoteApp(IApplication)`，动词分派）、`appenv.py`（`CX_NOTE_STYLES` + `console.push_theme`）、`app_help.py` + `help.md`/`help.en_US.md`、`i18n/`（domain `cx-note`）
- 现行的写路径是"边做边落盘"：`NoteStore.add` / `transition` / `erase` / `clear_domain` / `clean` 各自在末尾调用 `_save()`（`note_store.py:100`，tmp + `os.replace` 整文件重写）。批量 `add` 是每条各落一次盘，`clean()` 有清理时再落一次
- 现行的条目渲染是"整域一张表"：`_domain_table` 把该域全部条目塞进一个无框三列表（标号 / 内容 `ratio=1` / ID 徽章 `width=4` 右对齐）。内容列未设 `overflow`，Rich 列默认 `ellipsis` ⇒ 超长内容被截断；多行内容走 `Markdown`，CommonMark 软换行把多个源行并成一行（两个现象在本次设计阶段实测均成立）
- 现行回显 `_echo_list` 打印当前域直属条目全量；ID 定位是全库的（`find_by_id` 遍历全部条目），命中域外条目时回显里看不到它
- `say()` 走 stderr（`IAppEnvironment` 的 Console 以 `stderr=True` 构造，stdout 留给数据管道），`--json` 用内置 `print` 直出 stdout
- 框架侧 `IApplication` 只提供 `start()` / `run()` / `stop()` / `__exit__`，无收尾钩子；`run()` 是工具自己的方法
- 仓库无测试基础设施（AGENTS.md 明载：不得尝试运行测试命令），验证以实际运行为准；真实笔记库位于 `~/.config/cx-studio/CxNote/notes.json`，冒烟不得污染
- 无新第三方依赖

## Goals / Non-Goals

**Goals:**

- 运行阶段显式化：动词只改内存工作集；超龄清理与落盘收归收尾，一次原子重写
- 条目成为自足的呈现单元（条目块），任何呈现条目的场合复用同一形态；超长内容折行不截断、多行内容逐行呈现且与内容列对齐
- 回显报告本次变更条目（按所属域分块），跨域命中的条目可见
- 新增 `edit`；即将被清理的条目在呈现中带标记；清理按统一形态报告
- 域标题样式登记为主题字段

**Non-Goals:**

- 磁盘格式改动（`notes.json` 仍是裸 JSON 数组，不加版本头、不加域表）
- 域语义与定位规则（现状即目标态，本次不动）：单一全局库、域是条目的字面标签、cwd 只用于推导缺省域、`-g` 是根域快捷写法、4 位 ID 全库定位、文本片段限可见域（当前域及其下级域）
- 框架层改动（`cx-tools` 能力域零改动，不加 finalize 钩子）
- 条目改域（`move`）、手动清理命令、`$EDITOR` 交互编辑
- `--json` 的 stdout 契约与退出码语义调整
- 测试基础设施搭建（仓库无测试基建，不在本变更内引入）

## Decisions

### D1. 运行阶段落在 cxnote 自己的 application 层，框架零改动

`CxNoteApp.run()` 显式三段：

```
run()
├── 初始化      参数解析已在 appcontext；帮助路由；配置缺省初始化（保持现状）
├── 读盘        store = NoteStore(...)；now = datetime.now()（本次运行共用）
├── 处理业务    动词分派：只改 store 的工作集 + 打响应（人读回显 / --json）
└── 收尾        _finalize(store, current, retention, now)：超龄清理 → store.flush()
```

依据：`run()` 本就是工具自己的方法，阶段编排不需要框架配合；给 `IApplication` 加 finalize 钩子会牵动其余 6 个工具的骨架与 `cx-tools` 域 spec，收益为零。异常路径天然正确——异常从 `run()` 抛出后不再回到收尾，`__exit__` 只做既有的 `SafeError`/`KeyboardInterrupt` 呈现，磁盘保持原状。

### D2. 存储层改为「工作集 + 显式落盘」

`NoteStore` 保留"构造即全量读入内存"与损坏拒载，改动集中在写路径：

- **去掉**各写方法内部的 `_save()`；`_save()` 收敛为公开 `flush() -> bool`（脏标记为真时按 tmp + `os.replace` 整文件重写；返回是否写盘）
- **`clean()` 整体移除**——清理的判据与作用域属于运行上下文（保留天数、当前域、`now`），不该寄生在存储层。store 不再感知保留天数
- **改名与语义对齐 take**：`erase(eid)` → `take(eid)`，`clear_domain(domain)` → `take_domain(domain)`；两者只从工作集取走并把取走的条目交出来（回显被删条目的依据），不落盘
- 新增 `set_content(eid, content) -> Entry | None`（`edit` 用；内容与原文相同时照样返回并计入本次变更条目，只是不置脏、不落盘）、`take_many(entries) -> list[Entry]`（收尾清理用，按 id 取走）
- 脏标记只由"结果确有变化"的变更置位（`edit` 改出同内容、取走空集时都不置位），落到 spec 的"工作集与读盘结果一致时 MUST NOT 写盘"
- `add` 的批内去重回执、`transition` 的终态打点逻辑原样保留

### D3. 即将被清理：单一判据的纯函数 + 运行上下文

新增 `common/expiry.py`：

```python
def is_expiring(entry, scope, retention_days, now) -> bool
```

判定 = 终态（`done`/`dropped`）且终态打点非空且 `completed_at <= now - retention_days` 且 `is_within(entry.domain, scope)`；`retention_days <= 0` 恒为假（清理禁用 ⇒ 无标记、无清理）。

- `now` 在 application 层取一次、整 run 共用：同一 run 内呈现层与收尾清理的判定必然一致
- **不**在读盘时算成字段：判据依赖保留天数、作用域与当前时刻（读盘时未必齐备），且工作集在业务阶段会被改（`reset` 把条目拉回待办、`finish` 重打点都会让判定立刻反转）。`Entry` 与 `notes.json` 都不含该概念
- 消费方有三处、判据只有一份：呈现层标词、`--json` 的输出投影、收尾清理筛选工作集。**`common/entry.py` 不动**——`entry_to_json` 保持"持久化形态"的单一职责，`expiring` 由 application 层在输出投影时附加（`{**entry_to_json(e), "expiring": True}`）。被取走的条目（`erase` / `clear` 的输出）不带该键：收尾不会再清除它们

### D4. 条目块：每块一个无框三列表

`components/list_view.py` 重写渲染层：

- `make_entry_block(entry, expiring=False) -> r.Table`：三列 = ID（`width=4`，逐字符着色徽章，左对齐）/ 状态标号（自然宽）/ 内容（`ratio=1`）；`box=None`、`expand=True`；内容列显式 `overflow="fold"` 关掉 Rich 默认的 ellipsis 截断
- 列表 = 域标题行 + 逐条目块；`_domain_table`（整域共享表）删除——跨条目对齐随共享表一起消失
- **多行内容**：保留 Markdown 解释（既有决策：`- ` 等语法可用），但软换行 MUST 变硬换行。实现路径二选一，以实测选定（验收判据即 spec 场景「多行内容逐行呈现」）：(a) 把源行按硬换行连接后再交给 `Markdown`；(b) 多行内容改用保留换行的 `Text`（放弃 Markdown 解释）。默认取 (a)，(a) 实测不成立则退 (b)
- 终态弱化不变：已取消整体 dim + strike，已完成徽章随行 dim；多行内容仍不置灰（既有决策）
- `build_list_renderable` 增加两点：子树外域的标题 MUST 用绝对字面（现行 `_rel_label` 假定域在当前域之下，子树外会切出乱码）；是否补齐"当前域空块"由参数控制（列表要、回显不要）
- **即将被清理标记的传递**：渲染函数不感知保留天数与 `now`——application 在渲染前用 `is_expiring` 算一次 `expiring_ids: set[str]`，作为参数交给渲染函数（`make_entry_block(entry, expiring=entry.id in expiring_ids)`）；`--json` 的输出投影用同一集合附加 `expiring` 键。人读与 JSON 因此共享同一个判定结果
- 条目块的元素次序相对现状是**重排**（现行是 标号 / 内容 / ID 徽章，新形态是 ID / 标号 / 内容），这一重排是本次变更的可见变化之一

### D5. 即将被清理标记的位置与样式

- 词形 `即将被清理`（i18n msgid），JSON 键 `expiring`
- 位置：条目块首部的标号之后（`cnf5 [x] 即将被清理 …`）——即划入标号列内的一个附加段，**不新增列**；不动内容列，避免与多行内容相互挤压；标记为空时该段不占位
- 样式登记为 `CX_NOTE_STYLES["cx.note.expiring"]`（建议 `"yellow"`），渲染代码只写样式名
- 依据：用户定案——样式必须登记为主题字段，不得裸写在渲染代码里

### D6. 域标题样式与死样式清理

- `CX_NOTE_STYLES["cx.note.section"]`：`"bold"` → `"bold yellow"`（所有域标题共用：当前域、下级域、回显里的域块）
- 删除 `CX_NOTE_STYLES["cx.note.id"]`——全仓无引用，留着会让人误以为 ID 徽章走主题
- 不做格式改动：计数仍只有下级域带（`cx.note.hint`）、不加符号与分隔线

### D7. 回显组装：本次变更条目按域分块

application 层为每个动词累积"本次变更条目"，交给与列表同一套渲染：

| 动词 | 变更条目 |
|---|---|
| `add` | 新建条目 + 「已存在」回执条目，按参数序 |
| `finish` / `pend` / `reset` / `drop` | 转移后的条目 |
| `edit` | 覆盖后的条目 |
| `erase` | 被取走的条目（按取走前的状态呈现） |
| `clear` | 被取走的条目 |
| 收尾清理 | 被清理取走的条目（在回显之后单独报告） |

- 块间次序：当前域子树居前、其余按域身份（`canonical`）排序；块内次序：本次操作的处理顺序（与确认行 ID 列表对应）
- 不注入空的当前域块（回显场景）；无变更条目时整段不打印（确认行已述结果）
- 确认行、失败路径不回显、`--json` 不回显——沿用现行实现
- 依据："变更条目集合"是内存工作集模型的自然产物（被取走的条目对象就在手上），不需要反推或二次读盘

### D8. `edit` 的实现

- 参数面：`edit` 恰好两个参数（第一 = 目标、第二 = 新内容）；个数不符报 `SafeError` 中止，不执行任何修改
- 目标解析：现行 `_resolve_targets(store, current)` 直接读 `self.context.arguments`（`application.py:339`）——`edit TARGET CONTENT` 下它会把第二参数（新内容）当成第二个目标。接口改为 `_resolve_targets(store, current, targets=None)`（缺省取 `context.arguments`），`edit` 传 `targets=self.context.arguments[:1]`；`\n` → 真实换行同 `add`
- 落 `store.set_content(eid, content)`；不做去重/撞车校验，不改状态、域、ID、创建时间、终态打点
- 确认行 `已修改 {count} 条：〈ID 列表〉`；`--json` 输出单元素条目数组

### D9. 定位候选改用条目块

删除 `_content_preview`（首行 60 字截断预览），多义命中的候选逐条以条目块呈现。依据：spec 已要求"任何呈现条目的场合 MUST 使用条目块，MUST NOT 另立截断预览形态"。

呈现通道：`SafeError` 只携带字符串，而 `__exit__` 用 `say(f"[{style}]{exc}[/]")` 包样式——要在错误路径上渲染条目块，走工具侧（`cx_note/application.py`）：定义一个携带 `renderable` 的 `SafeError` 子类，`CxNoteApp.__exit__`（本就是工具自己的覆盖）在捕获到它时先 `say()` 该 renderable、再呈现摘要文本。框架 `cx-tools` 不动。

### D10. i18n 与帮助同步

- 新增 msgid：`即将被清理`、`已清理 {count} 条：`、`已修改 {count} 条：`、`edit 需要恰好两个参数（目标与新内容）` 等错误文案
- `app_help.py` 分组与 `help.md` / `help.en_US.md` 教程补 `edit`（八动词 → 九动词），教程同时修订"回显"的描述
- 依 `docs/agents/i18n.md` 的提取/更新/编译流程产出 `.po` / `.mo` 并一并提交

### D11. 验证策略：隔离 home 下的端到端实跑

仓库无测试基建，验证以实际运行为准，两条硬约束：

1. **隔离 home**：冒烟必须把用户主目录指向临时目录（Windows 上设 `USERPROFILE`），否则会读写真实的 `~/.config/cx-studio/CxNote/notes.json`。真实笔记数据不得用于试探
2. **取证留痕**：每条断言以实跑输出与磁盘内容为证（stdout 与 stderr 分开采集，`--json` 另看 stdout 纯净性）

覆盖点：条目块（超长折行、多行逐行、续行对齐）、列表与回显的域分块（含跨域命中）、`edit`（正常、参数个数错误、改出重复内容）、即将被清理的标记与收尾清理报告、`--json` 六键 + `expiring` + stdout 纯净、中途失败不落盘、只读运行也执行清理。

## Risks / Trade-offs

- **落盘在响应之后**（用户既定顺序）：响应已打印而落盘失败时，用户看到"成功"字样、磁盘未变。按既有 `SafeError` 语义报告到 stderr（仓库惯例：错误走 stderr、`--json` 消费者以 stdout 内容为准），退出码语义不在本变更内调整。若将来需要脚本可判定的失败信号，另立变更
- **整轮变更可能在收尾前丢失**：落盘只发生在收尾，进程被强杀（SIGKILL、断电——`__exit__` 不介入）会丢掉本轮全部变更。这是"内存为中心"的固有代价，换来的是"磁盘上永不出现半成品"；用户中断（SIGINT）不走这条路，异常路径本就不落盘，语义一致
- **Markdown 硬换行**依赖 Rich/markdown-it 的硬换行支持，实现时必须实测；不成立则退回 `Text` 方案（判据不变，代价是失去 `- ` 等 Markdown 解释）
- **每块一个 Table** 的渲染开销高于单表，条目数量在百量级时无感；列表密集度靠块内单行而非共享表维持
- **确认行与块序可能不同序**：确认行的 ID 列表按参数序、块按域分组（域组间按域排序），跨域批量操作时两者顺序不一致。接受——确认行是本轮处理清单，块是条目形态
- **清理报告出现在最末**：只读运行的清理报告会落在列表之后，需要读者习惯"最后一行是维护播报"
- **`--json` 中该标记是条件键**：与"六键全量在场（消费方不需探测）"的既有契约风格不同；理由是该键描述的是运行时条件（本次收尾是否会清掉它），不是条目固有属性，恒在场会让所有消费方都读一个绝大多数为假的字段
