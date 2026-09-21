# Proposal

## Why

仓库的规范体系仍由 ask-matt 技能框架驱动：工作项走 `.scratch/` 本地追踪器 + triage 分诊，设计决策按时间排进 25 篇编号 ADR 编年体。维护现行系统时查询主轴是「什么对象」而非「何时决定」，行为契约散落在 ADR 与 AGENTS.md 之间，`openspec/` 已初始化却空置。需要把 OpenSpec 确立为唯一规范框架：specs 按域聚合现行行为作为唯一真相源，变更走 delta 流程，旧体系整体退役。

## What Changes

- **退役 ask-matt 派生规范**：`docs/agents/issue-tracker.md`（含 wayfinding 操作）与 `docs/agents/triage-labels.md` 整体退役；`AGENTS.md` 中「Issue tracker」「Triage labels」两节及相关条款改写为 OpenSpec 工作流；`docs/agents/domain.md` 开篇的技能引用（`/domain-modeling`、`/triage`、`/to-spec`）改写；`.scratch/` 追踪内容清除。**BREAKING**：工作项入口从 `.scratch/` 票变更为 openspec 变更流程，triage 状态词汇与票生命周期不复存在。
- **立 OpenSpec 治理规范**：`openspec/config.yaml` 的 `context:` 填充项目背景指针；确立决策记录多轨体例（行为与协议→OpenSpec 变更流程、术语与约定→`CONTEXT.md`、全局纪律→`AGENTS.md`）。
- **ADR 重铸为主 specs**：25 篇编号 ADR 按「现行行为契约」判据分流重铸进四个行为域 spec；非行为内容归位 `CONTEXT.md` / `AGENTS.md`；无现行效力的内容退役。重铸完成后 `docs/adr/` 目录整体退役，全仓清除 ADR 编号引用。**BREAKING**：`docs/adr/` 编号体系消失，外部如有对 ADR 编号的引用将失效。

## Capabilities

### New Capabilities

- `norms`: 仓库规范治理体制——真相源归属、变更流程、决策记录多轨、领域文档布局与消费规则
- `cx-studio`: 基础设施库（时间域、FFmpeg、文件系统、IO、系统抽象）现行行为契约，自 ADR-0001 等重铸
- `cx-wealthy`: Rich UI 组件库（document 核心、help 特化层、渲染协议、命名与扩展原则）现行行为契约，自 ADR-0002~0010 重铸
- `cx-tools`: 应用生命周期框架（构造注入、Context 上下文管理器、组件依赖规则）现行行为契约，自 ADR-0011~0018 重铸
- `cxnote`: cxnote CLI（域模型、条目状态机、命令面行为、批量语义、展示与回显）现行行为契约，自 ADR-0019~0025 重铸

### Modified Capabilities

（无——`openspec/` 当前无任何主 specs，本变更全部为新增能力。）

## Impact

- **规范文档**：`AGENTS.md`（文档地图、决策先行条款、Issue tracker / Triage labels 两节）、`docs/agents/domain.md`、删除 `docs/agents/issue-tracker.md` 与 `docs/agents/triage-labels.md`、删除 `docs/adr/` 全目录。
- **OpenSpec 骨架**：`openspec/config.yaml`（填充 `context:`）、`openspec/specs/` 新增五个能力域。
- **本地文件**：`.scratch/`（gitignored）追踪内容清除。
- **代码**：不涉及任何 `packages/` 代码变更；包行为契约以现行实现为准重铸，不随本变更改动。
