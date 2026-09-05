# Issue tracker：本地 markdown

本仓库的 issue 与 spec 以 markdown 文件跟踪于 `.scratch/` 目录。`.scratch/` 已在 `.gitignore` 中忽略——票是本地文件，不随仓库提交、不进 git 历史；可追溯性由文件自身承载（`Status:` 行 + `## Comments` 段）。2026-09 之前的工作项在 GitHub Issues（`LambdaXIII/cx-studio-tk`），已全部关闭，保留作历史存档，不再新建。

## 约定

- 一个特性一个目录：`.scratch/<feature-slug>/`
- 该特性的 spec：`.scratch/<feature-slug>/spec.md`
- 实施票一票一文件：`.scratch/<feature-slug>/issues/<NN>-<slug>.md`，`NN` 从 `01` 递增，不复用
- 票文件顶部 `Status:` 行记录状态（取值见 `triage-labels.md`）
- 评论与讨论历史追加到文件底部 `## Comments` 标题下：`- **<日期> <作者>**：<内容>`

## 生命周期

开放票：`Status` 为五个 triage 角色之一（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human`）。
终态：`implemented`（已实现落地）或 `wontfix`（判定不处理）。终态票不参与开放票查询。

### 落地操作（实现完成后执行）

`ready-for-agent` 的票实现完成后，由实现者按以下步骤收尾：

1. 在 `## Comments` 下追加落地条目：`- **<日期> <执行者>**：实现摘要（涉及文件；若产生新设计决策，注明新 ADR 编号）`
2. 将文件顶部 `Status:` 改为 `implemented`
3. 实现中产生的新设计决策，先落一篇根级 `docs/adr/` ADR，再在步骤 1 的条目中引用其编号

`wontfix` 判定后保留 `Status: wontfix` 即终态，不额外动作。落地/判定后不删除票文件、不移动位置——编号与路径保持可追溯。

## 当技能说"发布到 issue tracker"时

在 `.scratch/<feature-slug>/` 下新建文件（目录不存在则创建）：spec 写 `spec.md`，票写 `issues/<NN>-<slug>.md`。

## 当技能说"获取相关 ticket"时

读取引用的票文件路径（用户通常直接传路径或票号）。

## Wayfinding 操作

供 `/wayfinder` 使用。map 是一个文件，子票一票一文件：

- **Map**：`.scratch/<effort>/map.md`（Notes / Decisions-so-far / Fog 正文）
- **子票**：`.scratch/<effort>/issues/NN-<slug>.md`，从 `01` 编号；`Type:` 行记录类型（`research`/`prototype`/`grilling`/`task`），`Status:` 行记录 `claimed`/`resolved`
- **阻塞**：票顶部 `Blocked by: NN, NN` 行；所列票全部 `resolved` 后解除
- **前沿**：扫描 `issues/` 下开放、未阻塞、未认领的票，编号最小者胜出
- **认领**：工作前先存 `Status: claimed`
- **解决**：`## Answer` 标题下追加答复，置 `Status: resolved`，再向 `map.md` 的 Decisions-so-far 追加上下文指针（gist + 链接）

wayfinder 子票的 `claimed`/`resolved` 是其流程内部状态；`type: task` 子票实现完成后按上方「落地操作」置 `implemented` 收尾。
