# 领域文档

工程技能（`/domain-modeling`、`/triage`、`/to-spec` 等）探索代码库时消费本仓库领域文档的规则。

## 探索前阅读

- **根 `AGENTS.md`** —— 全局规范基线，并指引各 workspace 的领域文档位置
- **目标 workspace 的 `CONTEXT.md`** —— 该 workspace 的领域文档：定位、架构、约定、领域词汇。处理 `packages/` 下内容时必读
- **目标 workspace 的 `docs/adr/`** —— 该 workspace 的设计决策记录（架构选择、否决方案、边界决策）

本仓库无根级 CONTEXT.md / CONTEXT-MAP.md / docs/adr/——领域文档完全 workspace 化，不设置总的。文件不存在时静默跳过，不提示缺失，也不建议预先创建。

## 文件结构

本仓库是多 workspace 单仓（uv workspace），三个 workspace 相对独立，各自持有完整的领域文档：

```
/
├── AGENTS.md                              ← 全局规范 + workspace 指引
└── packages/
    ├── cx-studio/
    │   ├── CONTEXT.md                     ← 定位、架构、约定、词汇
    │   └── docs/adr/                      ← 设计决策（时间域与开放库原则等）
    ├── cx-wealthy/
    │   ├── CONTEXT.md                     ← 定位、渲染协议契约、词汇
    │   └── docs/adr/                      ← 设计决策（分层、双轨、否决方案）
    └── cxalio-studio-tools/
        ├── CONTEXT.md                     ← 定位、三层分层、编写模式、词汇
        └── docs/adr/                      ← 设计决策（构造注入、Progress 边界等）
```

## 使用词汇表的词汇

输出中命名领域概念（issue 标题、重构提案、假设、测试名）时，使用对应 workspace CONTEXT.md 中 Language 节定义的术语，不漂移为词汇表明确回避的同义词。

所需概念不在任何 CONTEXT.md 中时，这是信号——要么你在发明项目不用的语言（重新考虑），要么存在真实空白（记下，交给 `/domain-modeling`）。

## 冲突标记

输出与某 workspace 的 ADR 冲突时，显式提出而非静默覆盖：

> 与 cx-wealthy ADR-000X（…）冲突——但值得重新讨论，因为……

## 沉淀新内容

- 领域术语与约定 → 对应 workspace 的 `CONTEXT.md`
- 设计决策（架构选择、否决方案）→ 对应 workspace 的 `docs/adr/`，编号取现有最大值 +1
