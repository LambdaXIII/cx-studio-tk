# cxnote 命令面重设计：erase/clear 删除模型与 reset/pend/finish 状态动词

> 领域：cxalio-studio-tools（cxnote）· 适用范围：cxalio-studio-tools · cxnote

v1.1.0 发布后用户验收反馈：`clear`（删单条）与 `clean`（超龄清理）近形难分、`clear` 命名不传达删除语义（与 shell 清屏撞名），状态动词 `doing` 不符合用户口语（"进行中"），且帮助系统缺失（无 `WealthyHelp`/`help.md`，`-h` 仅 argparse 裸输出）。据此对 v1 动词面（`add/list/done/doing/reset/clear/clean/config`）整体重设计。

## 决策

- **删除职责三分**：
  - `erase <id|文本>`：物理删除**单条**条目（承接原 `clear` 单条语义；ID 定位全库、文本定位限可见域）。
  - `clear`：**清空当前工作域全部条目**（`-p` 可指定任意域；**不含子域**；执行前确认一次）。域级删除需求即由此承载，不设独立命令。
  - 自动清理：原 `clean` 手动命令**取消**——超龄已完成条目的清理仅作为保存时顺带的自动维护（仅当前域、尽力而为、未完成永不参与）。
- **状态动词与状态值对齐**：命令 `reset`（拨回待办）/ `pend`（标为进行中）/ `finish`（标为完成）；JSON `status` 值同步换为 `todo` / `pending` / `done`（`doing` 退役）。
- **`config` 命令取消**：`retention_days` 只经配置文件调整；首次运行时自动初始化配置文件。
- **不设旧动词 alias**：工具仅用户一人使用，双轨词汇违背修复初衷。
- **定位规则不变但文档化**：ID 全库精确、文本片段限可见域（当前域 + 下级域）——写入帮助与教程。
- **帮助系统补齐仓库规范**：`app_help.py`（`WealthyHelp` DSL 简要帮助 `-h`）+ `help.md` 教程（`--tutorial`），与其它 5 工具同构。

## 理由

v1 的 `clear`（删单条）在终端心智里是"清屏/清空"——用户试用时反复追问"clear 是删当前域还是删全局？删除域影响子域吗"，三轮讨论后仍无法在概念上区分 `clear`/`clean`；命名缺陷无法靠文档弥补。终版把 `clear` 名字归还给它的直觉语义（清空当前域），单条删除让位给直白的 `erase`，超龄打扫则彻底移出命令面、退回自动维护——删除三概念（单条/整域/自动）从此由三个相距足够远的表达承载。状态命令选用完整动作祈使词贴合用户口语（用户明确"我从来不说 doing，一直说进行中"），命令词与状态序列化值同源（`pend`↔`pending`）。帮助系统缺失是 v1 明知缺口（context 字段预留未启用），本次一并补齐——命令不可发现是三个症状共同的根因之一。

## Considered Options

- **保留 `clear`/`clean` 原名、靠帮助讲清**：被否——用户多轮仍混淆两者，语义缺陷不能靠文档弥补。
- **`rm`/`del`/`delete` 替代单条删除**：用户拍板 `erase`。
- **命令 = 状态名（`todo`/`doing`/`done` 当动词）**：被否——用户三态口语是"待办/进行中/完成"，`doing` 不是其用词；改用 `reset`/`pend`/`finish` 动作词。
- **`config` 子命令化或 flag 化**：被否——取消 `config` 命令，配置只走文件（`retention_days`）。
- **域级删除设独立命令或 `--recursive` flag**：被否——`clear` 即"清空当前工作域（`-p` 指定域、不含子域）"，域级需求零新增动词。
- **JSON `status` 值保持 `doing`**：被否——用户拍板同步换 `pending`（破坏性契约变更，接受）。
- **为旧动词保留 alias**：被否——避免词汇双轨。

## Consequences

- 破坏性 CLI 变更（动词换名、`status` 值 `doing`→`pending`）→ 用户最终拍板发布单元迭代至 **1.1.1**（幅度表按接口契约变更本判 major，以用户决策为准）。
- spec issue #1（v1 全案）动词面段落过时——修订记录见 issue 评论与本文档。
- CONTEXT.md 术语「清除」退役，拆分为「删除」（`erase` 单条）/「清空」（`clear` 整域）/「清理」（自动维护）。
- 无 `clean` 手动命令后，超龄清理只随写操作（add/转移/erase/clear 等保存路径）顺带执行；纯读取永不触发清理（完整实施契约见 spec）。
- `clear` 的确认交互为新行为：人读模式列出将清数量、请求 `y` 确认；`--json` 模式跳过确认、直接输出被清条目数组（脚本通道无 stdin 在场，spec US 29 定案）。
- `done`/`doing`/`clear`/`clean`/`config` 旧命令名在已发布脚本中的用法失效——本工具无第三方消费者，接受。
