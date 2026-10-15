# norms Specification

## Purpose
定义仓库的规范治理体制：各能力域现行行为的真相源归属、行为变更的提出与折回流程、设计决策的多轨归位规则，以及领域文档的统一布局。它是其余四个行为域 spec 得以成立的元规则层。

## Requirements

### Requirement: specs 是现行行为唯一真相源

每个能力域（`cx-studio` / `cx-wealthy` / `cx-tools` / `cxnote`）的现行行为契约 MUST 以 `openspec/specs/<capability>/spec.md` 为唯一权威。其他文档（AGENTS.md、CONTEXT.md、docstring）对同一行为的陈述与 spec 冲突时，MUST 以 spec 为准，并通过变更流程修正歧源，不得静默遵循旧源。

#### Scenario: 文档与 spec 冲突

- **WHEN** 任何文档或代码注释陈述的行为与某能力域 spec 冲突
- **THEN** 以该 spec 为准，并将冲突作为 openspec 变更提出以修正歧源

### Requirement: 行为变更走 OpenSpec 变更流程

对任何能力域现行行为的修改 MUST 以 openspec 变更提出：proposal 说明动机，delta specs（ADDED / MODIFIED / REMOVED Requirements）描述行为差量，archive 时差量 MUST 折回主 specs，历史留存于 `openspec/changes/archive/`。MUST NOT 绕过变更流程直接修改主 specs。

#### Scenario: 提出并落地一个行为变更

- **WHEN** 需要修改某能力域的现行行为
- **THEN** 创建 openspec 变更并在其 delta specs 中描述行为差量，archive 后主 specs 反映新行为且变更目录移入 archive

### Requirement: 设计决策按内容性质多轨归位

新产生的设计决策 MUST 按内容性质归位，不设编号 ADR 体系：术语与领域约定归 `CONTEXT.md` 对应 Domain 分区；跨领域全局纪律归 `AGENTS.md`；行为与协议变更归 OpenSpec 变更流程。仓库 MUST NOT 存在 `docs/adr/` 目录或 ADR 编号引用。

#### Scenario: 一条新设计决策产生

- **WHEN** 工作中确立一项新的设计决策
- **THEN** 按其性质写入 CONTEXT.md、AGENTS.md 或经由 openspec 变更流程落地，且不产生任何 ADR 编号或 `docs/adr/` 路径引用

### Requirement: 工作项以 openspec 变更跟踪

工作项（特性、修复、重构、迁移）MUST 以 `openspec/changes/` 下的变更承载，MUST NOT 使用本地 markdown 追踪器（`.scratch/` 票）、triage 状态词汇或编号工单。

#### Scenario: 出现新的工作项

- **WHEN** 需要跟踪一项待实施的工作
- **THEN** 为其创建 openspec 变更（含规划工件），不创建 `.scratch/` 票或 triage 标签

### Requirement: 领域文档统一根级布局

领域文档 MUST 保持仓库级单套根级布局：`AGENTS.md` 为全局规范基线，`CONTEXT.md` 按 `## Domain:` 分区承载定位、架构、约定与词汇，`openspec/specs/` 承载行为真相源，`docs/agents/` 承载工作流文档。MUST NOT 在 `packages/` 下分散领域文档。

#### Scenario: 新增领域文档

- **WHEN** 需要沉淀新的领域文档
- **THEN** 落入根级对应位置（AGENTS.md / CONTEXT.md 相应分区 / openspec specs / docs/agents），不在 workspace 目录下另立文档

### Requirement: 项目背景指针随规范体系维护

`openspec/config.yaml` 的 `context:` 字段 MUST 承载指向项目背景（定位、架构、约定）的浓缩内容，并在规范布局或权威归属变化时同步更新，使 openspec 工作流生成工件时始终读到现行体制。

#### Scenario: 规范布局变化

- **WHEN** 本仓库的规范文档布局或权威归属发生变化
- **THEN** `openspec/config.yaml` 的 `context:` 字段同步更新为指向现行体制的内容
