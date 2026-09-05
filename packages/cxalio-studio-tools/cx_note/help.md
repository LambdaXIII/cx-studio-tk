# cxnote 使用指南

> *终端里的快速便签——记的速度要快，看的眼球要少。*

## 简介

cxnote 是一个极简的终端笔记 / 待办工具。所有条目存在一个 JSON 文件里，按**域**组织；日常操作只有一个动词加一个参数：

```bash
cxnote add "买牛奶"      # 记一条
cxnote                   # 看当前域
cxnote finish 牛奶       # 做完划掉
```

## 域与工作域

**域**是条目的归属路径，形如 `/工作/项目A`。你当前所在的目录决定**工作域**：

- 在 `~/projects/app` 下运行 `cxnote add "修 bug"`，条目记入与该项目对应的域；
- 不带 `-p` / `-g` 时，一切命令都在当前工作域内进行；
- 列表默认只显示当前工作域的条目，下级域以标题行折叠展示（`--full` 展开）。

| 参数 | 作用 |
|---|---|
| `-p` / `--path` | 切换工作域：以 `/` 开头为绝对域，否则相对当前域；**对所有动词生效** |
| `-g` / `--global` | 直接在根域工作 |

```bash
cxnote -p /生活琐事 add "交水电费"   # 记到绝对域
cxnote -p /app/backend list          # 看另一个域
cxnote -g list --full                # 根域全览
```

## 命令一览

| 命令 | 参数 | 说明 |
|---|---|---|
| `add` | 文本 | 记录一条内容到当前工作域；内容里的 `\n` 会转换为换行；**同域已有完全相同内容时不重复记录**（回执既有条目） |
| `list` | —（缺省动词） | 按域分组显示条目；`--full` 展开下级域 |
| `finish` | ID 或文本片段 | 标记为已完成，打完成时间 |
| `pend` | ID 或文本片段 | 转入进行中 |
| `reset` | ID 或文本片段 | 重置为待办，清空完成时间 |
| `erase` | ID 或文本片段 | 删除单条 |
| `clear` | — | 清空当前工作域的直属条目（不含子域），交互确认一次 |

```bash
cxnote add "周末计划\n- 爬山\n- 采购"   # 多行条目
cxnote pend 爬山                        # 转入进行中
cxnote finish a1b2                      # 按 ID 完成
cxnote erase a1b2                       # 删除单条
cxnote clear                            # 清空当前域（会先问你）
```

## 状态流转

每条笔记有三种状态：`todo`（待办）→ `pending`（进行中）→ `done`（已完成）。

- 只有 `done` 持有完成时间；`reset` / `pend` 会清空它；
- 列表里的标号：`[ ]` 待办、`[~]` 进行中、`[x]` 已完成。

## 删除的三种方式

1. **`erase <id|文本>`** —— 删一条；
2. **`clear`** —— 清空当前工作域的直属条目（**不含子域**），人读模式确认一次，`--json` 模式跳过确认；
3. **自动清理** —— 没有手动清理命令：每次写操作（add / finish / pend / reset / erase / clear）都会顺带删除**超过保留期的已完成条目**。保留期由配置决定（见下文）。

## 定位规则

`finish` / `pend` / `reset` / `erase` 的参数可以是：

- **ID**：每条笔记有 4 位 ID（列表行尾徽章），**全库精确定位**；
- **文本片段**：只在**可见域**（当前域 + 下级域）内做包含匹配，且**必须唯一命中**——多个命中会列出候选并让你改用 ID。

## JSON 输出

加 `--json` 后 stdout 只有纯净 JSON（标题、提示、确认全部跳过），适合脚本消费：

```bash
cxnote list --json                 # 当前域条目数组
cxnote list --json --full          # 当前域 + 全部下级域
cxnote add "买票" --json           # 新条目对象（重复时返回既有条目，幂等）
cxnote finish a1b2 --json          # 更新后的条目对象
cxnote clear --json                # 被清空的条目数组（不确认）
```

条目对象六个键固定在场：`id` / `domain` / `content` / `status` / `created_at` / `completed_at`（未完成时 `completed_at` 为 `null`）。

## 配置文件

首次运行时在配置目录自动生成 `config.toml`：

```toml
retention_days = 30
```

- `retention_days`：已完成条目的保留天数，超龄条目在写操作时被自动清理；
- `0` 或负数表示禁用自动清理；
- 想调整保留期直接编辑该文件即可（没有 config 命令）。

## 获取帮助

```bash
cxnote -h            # 分组帮助
cxnote --tutorial    # 本教程
```

> *项目地址：https://github.com/LambdaXIII/cx-studio-tk*
