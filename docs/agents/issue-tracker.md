# Issue tracker：GitHub

本仓库的 issue 与 spec 以 GitHub issue 形式跟踪。所有操作使用 `gh` CLI。

## 约定

- **创建 issue**：`gh issue create --title "..." --body "..."`，多行正文用 heredoc
- **读取 issue**：`gh issue view <number> --comments`，用 `jq` 过滤评论并获取标签
- **列出 issue**：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`，配合 `--label` 与 `--state` 过滤
- **评论 issue**：`gh issue comment <number> --body "..."`
- **应用/移除标签**：`gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **关闭**：`gh issue close <number> --comment "..."`

仓库从 `git remote -v` 推断——在克隆内运行 `gh` 自动定位。

## PR 作为请求面

**PR 是否作为 triage 请求面：否**。（如本仓库将外部 PR 视为功能请求，改为 `yes`；`/triage` 读取此标记。）

设为 `yes` 时，PR 与 issue 走同一套标签与状态，使用 `gh pr` 等价命令：

- **读取 PR**：`gh pr view <number> --comments`，diff 用 `gh pr diff <number>`
- **列出外部 PR**：`gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments`，仅保留 `authorAssociation` 为 `CONTRIBUTOR`、`FIRST_TIME_CONTRIBUTOR` 或 `NONE` 的（丢弃 `OWNER`/`MEMBER`/`COLLABORATOR`）
- **评论/标签/关闭**：`gh pr comment`、`gh pr edit --add-label`/`--remove-label`、`gh pr close`

GitHub 的 issue 与 PR 共享编号空间，裸 `#42` 可能是任一种——用 `gh pr view 42` 判定，失败回退 `gh issue view 42`。

## 技能说"发布到 issue tracker"时

创建 GitHub issue。

## 技能说"获取相关 ticket"时

运行 `gh issue view <number> --comments`。

## Wayfinding 操作

供 `/wayfinder` 使用。**map** 是一个带 `wayfinder:map` 标签的 issue，正文承载 Notes / Decisions-so-far / Fog；**子 ticket** 是关联的 issue。

- **Map**：`gh issue create --label wayfinder:map`
- **子 ticket**：作为 GitHub sub-issue 关联到 map（用 `gh api` 操作 sub-issues 端点）；未启用 sub-issues 时，将子项加入 map 正文的任务列表，并在子项正文顶部写 `Part of #<map>`。标签：`wayfinder:<type>`（`research`/`prototype`/`grilling`/`task`）。被认领后 ticket 分配给负责的开发
- **阻塞**：GitHub 原生 issue 依赖——`gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`，其中 `<blocker-db-id>` 是阻塞方的**数据库 id**（`gh api repos/<owner>/<repo>/issues/<n> --jq .id`，不是 `#number` 或 `node_id`）。GitHub 经 `issue_dependencies_summary.blocked_by` 报告（仅开放阻塞方——实时门）。依赖不可用时，回退为子项正文顶部 `Blocked by: #<n>, #<n>` 行。所有阻塞方关闭后 ticket 解除阻塞
- **前沿查询**：列出 map 的开放子项（`gh issue list --state open`，限定 map 的 sub-issues/任务列表），剔除有开放阻塞方（`issue_dependencies_summary.blocked_by > 0`，或 `Blocked by` 行有开放 issue）或已有 assignee 的；map 顺序第一个胜出
- **认领**：`gh issue edit <n> --add-assignee @me`——会话的第一次写入
- **解决**：`gh issue comment <n> --body "<answer>"`，然后 `gh issue close <n>`，再把上下文指针（gist + 链接）追加到 map 的 Decisions-so-far
