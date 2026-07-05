# WealthyHelp 用法指南

## 1. 概述

`WealthyHelp` 是 `cx_wealthy` 提供的 CLI 帮助系统构建器。它基于 `WealthyDocument` 通用结构化文档引擎，专为命令行工具的帮助输出（usage + 参数详情）设计。

核心设计原则：

- **声明式构建**：通过 `add_action`、`add_group`、`add_command` 等方法声明帮助结构，无需手写格式化逻辑
- **主题透明**：渲染使用 `cx.help.*` 样式约定，由调用方通过 `rich.Console(theme=...)` 决定是否应用 `cx_wealthy.default_theme`
- **递归渲染**：usage 和 details 区域均基于树结构递归生成，天然支持嵌套子命令

## 2. 快速开始

```python
from cx_wealthy import WealthyHelp
from rich.console import Console
from cx_wealthy.theme import default_theme

help = WealthyHelp(prog="mytool", description="一个示例工具")
help.add_action("-o", "--output", metavar="DIR", description="输出目录")
help.add_action("INPUT", description="输入文件")

console = Console(theme=default_theme)
console.print(help)
```

渲染效果（示意）：

```
┌─ 用法 ─────────────────────────────────┐
│ mytool [-o|--output DIR] INPUT          │
│                                         │
│   一个示例工具                           │
└─────────────────────────────────────────┘
┌─ 参数详情 ──────────────────────────────┐
│     -o, --output  DIR  输出目录          │
│     INPUT  输入文件                      │
└─────────────────────────────────────────┘
```

## 3. 核心概念

### 3.1 继承体系

```
Node (document/node.py)
├── Action (help/action.py)     — 命令行选项/位置参数
├── Group (document/group.py)   — 通用容器
│   └── HelpGroup (help/help_group.py) — 帮助容器（参数分组 or 子命令）
└── Note (document/note.py)     — 注释/提醒文本

WealthyDocument (document/document.py)
└── WealthyHelp (help/help.py)  — 帮助系统入口
```

### 3.2 三层架构

| 层 | 模块 | 职责 |
|---|---|---|
| 通用核心 | `cx_wealthy.document` | Node/Group/Note/WealthyDocument 树结构和基础渲染 |
| 帮助特化 | `cx_wealthy.help` | Action/HelpGroup/WealthyHelp CLI 语义 |
| 主题样式 | `cx_wealthy.theme` | `cx.help.*` 样式预设（可选） |

### 3.3 WealthyHelp 与 WealthyDocument

`WealthyHelp` 继承 `WealthyDocument`，重写了 `render()` 方法，yield 三个区域：

1. **usage** — 用法行（`render_usage()`）
2. **details** — 参数详情（`render_details()`）
3. **epilog** — 尾部内容（`render_epilog()`）

## 4. Action 详解

`Action` 表示一个命令行参数——选项（如 `-o`、`--output`）或位置参数（如 `INPUT`）。

### 4.1 构造参数

```python
Action(
    *flags,              # 标志字符串
    name=None,           # 自然语言名称
    description=None,    # 描述文本
    metavar=None,        # 在 usage 中显示的占位符
    nargs=None,          # 参数个数：int / "?" / "+" / "*" / "**"
    optional=None,       # 显式指定是否可选（None=自动推断）
    prefix_chars="-",    # 选项前缀字符
)
```

### 4.2 选项 vs 位置参数

- **选项**：flags 以 `prefix_chars`（默认 `-`）开头 → `is_optional() == True`
- **位置参数**：flags 不以 `prefix_chars` 开头，或 flags 为空 → `is_positional() == True`

### 4.3 可选性判定

`is_optional()` 的判定逻辑（优先级从高到低）：

1. 构造时显式传入 `optional=True/False`
2. `is_positional() == False` → 可选
3. `is_positional() == True` 且 `nargs="?"` → 可选
4. 其它 → 非可选

### 4.4 usage 渲染规则

| 类型 | 示例 | usage 渲染 |
|---|---|---|
| 可选选项 | `-o, --output` | `[-o\|--output DIR]` |
| 必选选项 | `--name`（optional=False） | `--name VAL` |
| 位置参数 | `INPUT` | `INPUT` |
| 可选位置 | `INPUT`（nargs="?"） | `[INPUT]` |
| nargs="+" | `FILES`（nargs="+"） | `FILE1 [, FILE2 [, FILE3 ...]]` |
| nargs="*" | `FILES`（nargs="*"） | `[FILE1 [, FILE2 [, FILE3 ...]]]` |
| nargs="**" | `--define`（nargs="**"） | `[--define VAL] [--define ...]` |

### 4.5 details 渲染

details 行格式：`flags  metavar   description`，自动对齐。

## 5. HelpGroup — 帮助容器

`HelpGroup` 继承 `Group`，是表达 CLI 帮助结构的核心容器。它兼具两种角色，由 `commands` 字段是否为空决定：

| commands | 角色 | 说明 |
|---|---|---|
| 空 `()` | **参数分组** | 仅用于组织分组，不参与 usage 行命令列表 |
| 非空 `("list",)` | **命令本身** | 参与 usage 行的 pipe 列表拼接，如 `list\|show\|edit` |

`is_command` 属性（`bool(commands)`）区分两种角色。

### 5.1 参数分组用法

```python
help = WealthyHelp(prog="mytool")
basic = help.add_group("基本选项")
basic.add_action("-o", "--output", metavar="DIR", description="输出目录")
basic.add_action("-q", "--quiet", description="安静模式")

advanced = help.add_group("高级选项")
advanced.add_action("--scale", metavar="FACTOR", description="缩放比例")
```

details 区域按 Group 分组渲染：

```
┌─ 参数详情 ──────────────────┐
│ 基本选项                     │
│     -o, --output  DIR  ...   │
│     -q, --quiet  ...         │
│                              │
│ 高级选项                     │
│     --scale  FACTOR  ...     │
└──────────────────────────────┘
```

### 5.2 子命令用法

```python
from cx_wealthy import WealthyHelp, HelpGroup

help = WealthyHelp(prog="mytool")

# 全局选项
opts = help.add_group("全局选项")
opts.add_action("-h", "--help", description="显示帮助")

# 子命令
cmds = help.add_group("子命令")

list_cmd = cmds.add_command("list", description="列出所有项")
list_cmd.add_action("-s", "--search", metavar="PATTERN", description="搜索")

show_cmd = cmds.add_command("show", description="显示指定项")
show_cmd.add_action("ITEM_ID", metavar="ID", description="项目ID")
```

### 5.3 API 参考

#### WealthyHelp 层级

| 方法 | 返回 | 说明 |
|---|---|---|
| `add_action(*flags, ...)` | `Action` | 添加全局选项/位置参数 |
| `add_group(name, description)` | `HelpGroup` | 添加分组（参数分组或子命令容器） |
| `add_command(*keywords, name, description)` | `HelpGroup` | 创建顶层命令 |

#### HelpGroup 层级

| 方法 | 返回 | 说明 |
|---|---|---|
| `add_action(*flags, ...)` | `Action` | 添加专有参数（选项/位置参数） |
| `add_command(*keywords, name, description)` | `HelpGroup` | 添加子命令（嵌套） |
| `add_group(name, description)` | `HelpGroup` | 添加子分组容器（嵌套分组） |
| `add_note(content)` | `Note` | 添加注释文本（继承自 Group） |

### 5.4 嵌套命令

支持任意深度嵌套（git 风格）：

```python
cmds = help.add_group("子命令")
remote = cmds.add_command("remote", description="管理远程仓库")
remote_add = remote.add_command("add", description="添加远程仓库")
remote_add.add_action("NAME", description="远程名称")
remote_add.add_action("URL", description="远程地址")
```

## 6. 渲染输出

### 6.1 usage 区域

usage 区域自动适配命令结构：

- **无命令**：单行 `prog [options...] args`
- **有命令**：多行
  - 首行：简版总览（`prog cmd1|cmd2|cmd3 [全局选项]`）
  - 后续行：每个子命令的详版（`prog cmd1 [专有参数]`）

#### 递归算法图解

```
root (prog="mytool")
├── HelpGroup "全局" (参数分组)
│   ├── Action --help
│   └── Action --debug
└── HelpGroup "子命令" (参数分组，命令容器)
    ├── HelpGroup "list" (命令)
    │   └── Action --search
    └── HelpGroup "show" (命令)
        └── Action ITEM_ID

渲染：
  mytool list|show [-h|--help] [--debug]          ← 简版 (子命令在前)
  mytool list [-s|--search PATTERN]               ← 详版 (list)
  mytool show ITEM_ID                             ← 详版 (show)
```

每层的处理算法相同：
1. 收集直接子 Action → local_args
2. 收集直接子 HelpGroup（is_command=True）→ sub_commands（非命令容器递归展开）
3. 非命令 HelpGroup（commands=()）→ 其内含 Action 归入 local_args
4. 简版行：path + sub_commands pipe 列表 + local_args（optional→positional 排序）
5. 详版行：每个 sub_command 递归

### 6.2 details 区域

details 按以下顺序渲染：

1. root 下未分组的 Action（逐行详情）
2. root 下的非命令 HelpGroup（组标题 + 组内 Action 详情）
3. root 下的命令 HelpGroup（子命令区块）

命令 HelpGroup 的详情渲染：

- **参数分组**：标题 + 每个子命令的详情（缩进排列）
- **命令本身**：关键词 + 描述 + 专有参数详情
- **嵌套命令**：递归展开，逐层缩进

### 6.3 epilog 区域

尾部内容，渲染为居中文本。通常用于显示项目链接或维护信息。

```python
help = WealthyHelp(prog="mytool", epilog="[link https://example.com]项目主页[/]")
```

## 7. 主题样式

`cx_wealthy.theme` 提供以下 `cx.help.*` 样式预设：

| 样式名 | 默认值 | 用途 |
|---|---|---|
| `cx.help.usage.title` | `green` | usage 面板标题 |
| `cx.help.usage.prog` | `orange1` | 程序名 |
| `cx.help.usage.bracket` | `bright_black` | 方括号和 pipe 分隔符 |
| `cx.help.usage.option` | `cyan` | 选项名（如 `-o`） |
| `cx.help.usage.argument` | `italic yellow` | 参数占位符（如 `DIR`） |
| `cx.help.usage.command` | `bold magenta` | 命令关键词（如 `list`） |
| `cx.help.group.title` | `orange1` | 参数分组标题 |
| `cx.help.group.description` | `italic dim default` | 分组描述 |
| `cx.help.details.box` | `blue` | 面板边框 |
| `cx.help.details.description` | `italic default` | 参数描述文本 |
| `cx.help.epilog` | `dim italic default` | 尾部链接 |

```python
from cx_wealthy.theme import default_theme
console = Console(theme=default_theme)
```

不应用主题时，`cx.*` 样式静默不生效（Rich 默认行为），内容仍完整可读。

## 8. 完整示例

### 8.1 无子命令工具（jpegger 风格）

```python
help = WealthyHelp(prog="jpegger", description="批量图片转换工具")

basic = help.add_group("基本选项")
basic.add_action("INPUT", description="输入文件")
basic.add_action("-f", "--format", metavar="FORMAT", description="输出格式")

proc = help.add_group("图片处理")
proc.detail = "对图像进行处理"
proc.add_action("--scale", metavar="FACTOR", description="缩放比例")

other = help.add_group("其它选项")
other.add_action("--debug", description="调试模式")
other.add_action("-h", "--help", description="显示帮助")
```

usage 单行输出。

### 8.2 子命令工具（hosts_keeper 风格）

```python
help = WealthyHelp(prog="hostskeeper",
    description="hosts 文件管理工具")

# 全局选项
misc = help.add_group("杂项")
misc.add_action("-h", "--help", description="显示帮助")
misc.add_action("-d", "--debug", description="调试模式")

# 子命令
cmds = help.add_group("子命令")

list_cmd = cmds.add_command("list", description="列出配置文件")
list_cmd.add_action("-s", "--search", metavar="PATTERN", description="搜索模式")

show_cmd = cmds.add_command("show", description="显示配置文件")
show_cmd.add_action("PROFILE_ID", metavar="ID", description="配置文件ID")

update_cmd = cmds.add_command("update", description="更新 hosts")
update_cmd.add_action("--target", metavar="PATH", description="目标文件")
update_cmd.add_action("--skip-flush", description="跳过 DNS 刷新")
```

usage 多行输出（简版 + 详版）。

### 8.3 嵌套子命令（git 风格）

```python
help = WealthyHelp(prog="gitsim", description="精简版 Git")

cmds = help.add_group("子命令")

# 一级命令
remote_cmd = cmds.add_command("remote", description="管理远程仓库")
# 二级命令
remote_cmd.add_command("add", description="添加远程仓库")
remote_cmd.add_command("remove", description="删除远程仓库")
# 三级命令（演示）
branch_cmd = cmds.add_command("branch", description="管理分支")
list_branch = branch_cmd.add_command("list", description="列出分支")
list_branch.add_action("--remote", "-r", description="显示远程分支")
```

## 9. 迁移指南

### 从扁平结构迁移到 HelpGroup

**迁移前**（所有参数混在一个 Group）：

```python
opt_group = self.add_group("命令和参数")
opt_group.add_action("COMMAND", nargs="?", metavar="list|show|edit", ...)
opt_group.add_action("PROFILE_ID", optional=True, metavar="PROFILE_ID", ...)
opt_group.add_action("--search-pattern", "-s", ...)  # 只在 list 下有效
opt_group.add_action("--target", ...)                 # 只在 update 下有效
```

**迁移后**（子命令 + 参数归属）：

```python
# 全局选项（所有命令共享）移到单独的 Group
misc = self.add_group("杂项")
misc.add_action("-h", "--help", ...)
misc.add_action("-d", "--debug", ...)

# 子命令，每个带专有参数
cmds = self.add_group("子命令")
list_cmd = cmds.add_command("list", description="列出")
list_cmd.add_action("-s", "--search", metavar="PATTERN", ...)

show_cmd = cmds.add_command("show", description="显示")
show_cmd.add_action("PROFILE_ID", metavar="ID", ...)

update_cmd = cmds.add_command("update", description="更新")
update_cmd.add_action("--target", metavar="PATH", ...)
```

**迁移检查清单**：

- [ ] 删除伪装的 `COMMAND` 位置参数（由 HelpGroup 命令结构表达）
- [ ] 删除全局混入的 `PROFILE_ID`（由各子命令的专有参数表达）
- [ ] 将全局选项（`-h`、`--debug` 等）移到独立的参数分组
- [ ] 为每个子命令创建 HelpGroup，挂载其专有参数
- [ ] 检查参数名是否与 argparse 定义一致（如 `--search-pattern` → `-s, --search`）
- [ ] 检查是否有遗漏的子命令（如 `new`）
- [ ] 运行 `--help` 验证输出结构
