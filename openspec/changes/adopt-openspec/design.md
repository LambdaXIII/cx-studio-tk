# Design

## Context

`openspec/` 已初始化（spec-driven schema，无主 specs、无在途变更）；ask-matt 框架在仓库的残留为两份规范文件（`docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md`）、`AGENTS.md` 相关章节、`docs/agents/domain.md` 的技能引用与 `.scratch/` 本地追踪内容。25 篇编号 ADR 的领域标注已在 `docs/adr/README.md` 维护为五组，与 `CONTEXT.md` 的三个 Domain 分区同构。动机见 proposal.md。

## Goals / Non-Goals

**Goals:**

- OpenSpec 成为唯一规范框架：主 specs 按对象聚合现行行为，行为变更走 delta 流程
- ask-matt 派生规范零残留（规范文件、AGENTS.md 章节、`.scratch/` 内容、wayfinding 约定）
- 25 篇 ADR 内容全部归位后 `docs/adr/` 目录整体退役，全仓无 ADR 编号引用
- 迁移以单次原子提交收口，不把「specs 已立、ADR 未删」的双权威中间态送进历史

**Non-Goals:**

- 不改动 `packages/` 下任何代码与包的现行行为（spec 以现状为准重铸，不改实现）
- 不处理 GitHub Issues 历史（已关闭存档，维持现状）
- 不动 `docs/agents/i18n.md`（与 OpenSpec 无冲突）
- 不重构 `CONTEXT.md` 词汇表（仅在 ADR 内容需要归位时局部补充）
- 不引入 store、不改 openspec schema

## Decisions

### D1 域划分沿用 ADR 领域标注，不发明新切分

四个行为域 + 一个治理域：

| spec 域 | 来源 ADR | 内容 |
|---|---|---|
| `cx-studio` | 0001 | 时间域资产保护、公开 API 删除约束 |
| `cx-wealthy` | 0002–0010 | document/help 分层、渲染协议、依赖链、命名与扩展约束 |
| `cx-tools` | 0011–0018 | 构造注入、Context 上下文、组件依赖规则（域命名与包目录、导入前缀一致） |
| `cxnote` | 0019–0021, 0023–0025 | 域模型、条目状态机、命令面行为、批量语义、展示与回显 |
| `norms` | 0022 治理面 | 本变更 specs 增量已承载 |

理由：领域标注是已维护的事实，CONTEXT.md 分区与之同构；另立切分徒增映射成本。

### D2 重铸判据来自 OpenSpec 对 spec 的定义

spec 只收消费方可观察、可验证的行为契约（输入输出、错误条件、外部约束，RFC 2119 显式 + GIVEN/WHEN/THEN 场景）；「实现可变而外部行为不变」的内容不进 spec。ADR 是决策时快照，重铸以现行实现与现行文档为权威校准，与现状冲突的内容按现状落笔；若发现实现偏离应有契约，作为独立行为变更另立 change，不在本迁移中顺手改代码。逐类映射：

| ADR 内容性质 | 去向 |
|---|---|
| 行为/协议契约（批量语义、状态机、yield 渲染对象、构造注入行为面） | 域 spec 的 Requirement + Scenario |
| 可验证的外部约束（最小依赖链、不做 i18n、不做 argparse 包装器） | 域 spec 的约束性 Requirement |
| 决策方法论与纪律（扩展判断原则、诚实命名的原则面） | `CONTEXT.md` 定位/约定段或 `AGENTS.md` |
| 治理体例（0022 的文档布局面） | `norms` spec 与 `AGENTS.md` |
| 无现行效力或已被后续决策取代的内容 | 退役，不迁移 |

### D3 样本先行：cxnote 域先铸

cxnote 域内容最厚（五篇 ADR 交织出状态机 + 命令面 + 批量语义），先重铸它校准粒度与形态：域级单文件、约 10 Requirement / 30 Scenario 量级，`openspec validate --strict` 通过后再铺其余三域。粒度问题（拆细迫使消费方跨文件拼装）以样本实测为准，不预设。

### D4 统一形态前置

- 标题与正文语言：简体中文；`Requirement:` / `Scenario:` / WHEN/THEN 关键字保留英文（validate 解析所需）
- 行为主语用对外契约（CLI 动词、公开 API 的语义），内部类名仅必要时括注
- spec 正文自足：不引用 ADR 编号、`docs/` 路径、issue；跨域只留一句指向，不复述相邻域内容
- 每个域 spec 的 Purpose 一到两句说明该域覆盖面

### D5 退旧立新的顺序与收口

执行序：重铸四域 delta（全部在本变更内完成）→ 退旧（删两份规范文件、改写 AGENTS.md 与 domain.md、清 `.scratch/`、`docs/adr/` 整体退役、清 config.yaml 模板注释并填 `context:`）→ `openspec validate --strict` → 两轮引用扫描 → 单次原子提交。引用扫描第一轮扫 `docs/adr`、`ADR-\d{4}`、`.scratch`、`triage`、`issue-tracker`、`wayfinder`；第二轮在删除完成后复扫正文残留指称（「ADR 编号唯一」「triage 角色」类旧主语）。commit message 独立记清改了什么、为什么，不赘述 diff。

### D6 AGENTS.md 改写落点

- 文档地图：`docs/adr/` 行替换为 `openspec/` 行；`docs/agents/` 描述去掉 issue tracker 与 triage
- 「处理 workspace 前必读」清单：CONTEXT 分区 + 对应域 spec（替换 ADR）
- 「Agent skills」节：Issue tracker / Triage labels 两小节替换为 OpenSpec 工作流小节；Domain docs 小节保留但去 ADR 引用
- 决策先行条款改为多轨表述（行为→变更流程、术语→CONTEXT、纪律→AGENTS.md）
- 全文残留 ADR 引用逐处改写为独立陈述

### D7 config.yaml 的 context 内容

填充浓缩指针：仓库定位与三包依赖链、规范布局（AGENTS.md / CONTEXT.md / openspec/specs / docs/agents 各自承载什么）、行为真相源声明、i18n 源语言要点、领域文档消费规则。只放指针与要点，不复制文档内容——context 是导航，不是第二个真相源。

## Risks / Trade-offs

- **一次性重铸 25 篇工作量大**：样本先行 + 逐域推进 + validate 机械兜底；收口前不得部分提交，避免双权威中间态。若 apply 中途必须暂停，保留未收口的变更目录（而非提交半套体系）。
- **行为 spec 与贡献者纪律的边界在个别条目模糊**（展示协议、命名约定兼具两面）：按 D2 判据逐条裁定，拿不准时以「消费方能否观察」为试金石；裁定结果在 design 或 commit message 留一句理由。
- **中文正文与 openspec 解析器的兼容性**：形态约定（D4）固定关键字英文、内容中文，validate --strict 全域通过作为机械验证。
