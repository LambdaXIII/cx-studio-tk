# Triage 标签

技能以五个规范 triage 角色表达概念；本地 markdown 追踪器中，triage 状态通过票文件顶部的 `Status:` 行表达。本文件将角色映射为实际写入 `Status:` 行的字符串，并声明第六个落地标签。

| 技能角色 | 本仓库 `Status:` 值 | 含义 |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | 维护者需要评估该票 |
| `needs-info` | `needs-info` | 等待报告者补充信息 |
| `ready-for-agent` | `ready-for-agent` | 已充分描述，可交给 agent 实现 |
| `ready-for-human` | `ready-for-human` | 需要人类实现 |
| `wontfix` | `wontfix` | 不会处理（自身即终态） |

技能提到某个角色（如"应用 ready-for-agent 的 triage 标签"）时，将票文件顶部 `Status:` 行写为表中对应值。

## 落地标签：implemented

除五个 triage 角色外，词汇表含第六个状态标签 `implemented`——票实现完成后置此收尾，表示「已落地」。它不是待评估角色，不用于新票。落地操作规范见 `issue-tracker.md` 的「落地操作」。

状态词汇变化时直接编辑本文件。
