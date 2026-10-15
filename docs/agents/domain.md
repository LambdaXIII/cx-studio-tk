# 领域文档

工程技能（`/domain-modeling` 等）探索代码库时消费本仓库领域文档的规则。

## 布局：仓库级单套

领域文档不按 workspace 分散，统一存放于仓库根级：

```
/
├── AGENTS.md      ← 全局规范基线（跨领域通用规则，含各 workspace 指引）
├── CONTEXT.md     ← 仓库统一领域文档：定位、架构、约定、领域词汇（按 `## Domain:` 分区）
├── openspec/      ← 规范框架：specs/ 按能力域承载现行行为契约（唯一真相源）；changes/ 承载在途行为变更
└── packages/      ← 代码本体；不再携带领域文档
```

适用范围在内容中声明，不靠目录位置区分：每个 `## Domain:` 分区标注适用领域（cx-studio / cx-wealthy / cxalio-studio-tools / 全局），每个能力域 spec 以能力名对应包。

## 探索前阅读

1. 根 `AGENTS.md`——全局规范基线
2. 根 `CONTEXT.md`——处理 `packages/` 下某 workspace 内容时，阅读该 workspace 对应的 `## Domain:` 分区（定位、架构、约定、词汇）
3. `openspec/specs/`——阅读适用该 workspace 的能力域 spec（现行行为契约的唯一真相源）

文件不存在时静默跳过，不提示缺失，也不建议预先创建。

## 使用词汇表的词汇

CONTEXT.md 的词汇表按 Domain 分区。输出中命名领域概念（issue 标题、重构提案、假设、测试名）时，使用目标 Domain 词汇表中定义的术语，不漂移为同义词。

所需概念不在任何 Domain 词汇表中时，这是信号——要么你在发明项目不用的语言（重新考虑），要么存在真实空白（记下，交给 `/domain-modeling`）。

## 冲突标记

输出与某能力域 spec 或 CONTEXT.md 陈述冲突时，显式提出而非静默覆盖（指明能力域名与 Requirement 标题）：

> 与 <capability> spec 的「<Requirement 标题>」冲突——但值得重新讨论，因为……

## 沉淀新内容

- 领域术语与约定 → 根 `CONTEXT.md` 对应 Domain 分区
- 行为与协议变更 → openspec 变更流程（`openspec/changes/`，delta 描述行为差量）
- 跨领域全局纪律 → 根 `AGENTS.md`
