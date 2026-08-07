[English](README.en.md) | 简体中文

# cx-wealthy

基于 [Rich](https://github.com/Textualize/rich) 的终端结构化文档与 UI 组件库。

为领域对象提供标签与详情两种渲染模式，让结构化输出声明式构建——不手写 Table/Panel 拼装，不继承 Rich 内部协议。

## 安装

```bash
pip install cx-wealthy
```

在 uv 项目中引入：

```bash
uv add cx-wealthy
```

## 核心概念

### 标签与详情渲染协议

cx-wealthy 为 Rich 扩展了两种渲染模式：`__rich_label__`（紧凑标签，用于行内摘要）和 `__rich_detail__`（键值面板，用于结构化详情）。继承对应的 mixin 后，`console.print()` 自动以该模式渲染——无需在调用点手动包装。

```python
from cx_wealthy import RichLabelMixin, RichDetailMixin, WealthyDetailPanel
from rich.console import Console

console = Console()

class Mission(RichLabelMixin, RichDetailMixin):
    def __init__(self, name, source, overwrite=False):
        self.name = name
        self.source = source
        self.overwrite = overwrite

    def __rich_label__(self):
        yield "[bold]M[/]"
        yield self.name
        yield f"→ {self.source}"

    def __rich_detail__(self):
        yield "名称", self.name
        yield "源文件", str(self.source)
        yield "覆盖", self.overwrite, False        # 三元组：值等于默认时不显示

console.print(Mission("encode", "input.mp4"))
# 输出标签：M encode → input.mp4

console.print(WealthyDetailPanel(Mission("encode", "input.mp4")))
# 输出键值面板，"覆盖"行因 overwrite==False 被去重隐藏
```

不愿继承时，用包装器 `RichLabel(obj)` / `WealthyDetailPanel(obj)` 渲染任意实现了协议的对象。

**`__rich_detail__` yield 格式：**

| 元组形态 | 效果 |
|---|---|
| `(key, value)` | 显示 `key = value` |
| `(key, value, default)` | `value == default` 时该行不显示 |
| `(value,)` | 仅显示值，key 列为空 |
| `(key, *values)` | value 为列表 |

**字符串与 markup**：`str` 类型的 key/value 逐字显示（不解析 markup）；需要 markup 格式时 yield `Text.from_markup(...)`。

`__rich_detail__` 与 Rich 原生 `__rich_repr__` 语义不同：后者是 debug repr（raw 值 + Pretty 渲染），前者是展示视角（value 可预格式化、支持递归嵌套 sub-panel、列表自动渲染为 `IndexedListPanel`）。

### 声明式文档构建

通过 `Node` → `Group` + `Note` 的复合树构建结构化文档，`WealthyDocument` 组织渲染。帮助系统是其中的特化层——`WealthyHelp` 继承 `WealthyDocument`，增加 `Action` 节点和 usage/details 渲染。

```python
from cx_wealthy import WealthyHelp

help = WealthyHelp(prog="myapp", description="CLI 工具说明")
help.add_action("--input", metavar="FILE", description="输入文件路径")
help.add_action("--output", metavar="FILE", description="输出文件路径")
help.add_action("--verbose", description="详细输出")
help.add_note("使用 --help 查看完整用法。")
console.print(help)
```

`WealthyHelp` 自动渲染 usage 行（选项按可选/位置分组）、参数详情表格、epilog 尾部。

`WealthyDocument` 不限于帮助系统——任何"分组 + 条目 + 注释"的结构化输出都可以用它构建。

### 子命令结构

对于有子命令的 CLI 工具（如 `git`/`docker` 风格），使用 `HelpGroup` 表达：

```python
commands = help.add_group("子命令")
list_cmd = commands.add_command("list", description="列出所有项")
list_cmd.add_action("-s", "--search", metavar="PATTERN", description="搜索过滤")

update_cmd = commands.add_command("update", description="更新")
update_cmd.add_action("--force", description="强制更新")
```

`WealthyHelp` 自动渲染多行 usage（简版总览 + 每个子命令详版）和按命令分组的参数详情。

## 辅助组件

| 组件 | 用途 |
|---|---|
| `IndexedListPanel` | 带行号索引的列表面板，支持截断（`max_lines=None` 不限） |
| `MaxColumnsLayout` | 固定最大列数的多列布局 |

```python
from cx_wealthy import IndexedListPanel, MaxColumnsLayout

console.print(IndexedListPanel(["a", "b", "c"], title="文件列表"))
console.print(MaxColumnsLayout(["one", "two", "three", "four"], max_columns=3))
```

## 主题预设

`cx.*` 命名空间的 Rich 主题样式。

```python
from cx_wealthy.theme import default_theme
from rich.console import Console

console = Console(theme=default_theme)
console.print("[cx.success]操作成功[/]")
console.print("[cx.error]操作失败[/]")
```

| 样式 | 效果 |
|---|---|
| `cx.success` | 粗体绿色 |
| `cx.error` | 粗体红色 |
| `cx.warning` | 粗体黄色 |
| `cx.info` | 青色 |
| `cx.whisper` | 暗色 |
| `cx.number` | 青色 |

## Rich 类型便利出口

```python
from cx_wealthy import rich_types as r

table = r.Table(show_header=True)
table.add_column(r.Column("名称"))
r.Console().print(table)
```

## 模块索引

| 模块 | 导出 |
|---|---|
| `label` | `RichLabelMixin` · `RichLabel` |
| `detail` | `RichDetailMixin` · `WealthyDetailTable` · `WealthyDetailPanel` |
| `document` | `Node` · `Group` · `Note` · `WealthyDocument` |
| `help` | `Action` · `HelpGroup` · `WealthyHelp` |
| `indexed_list` | `IndexedListPanel` |
| `columns` | `MaxColumnsLayout` |
| `theme` | `CX_STYLES` · `HELP_STYLES` · `default_theme` |
| `rich_types` | Rich 高频类型别名出口 |

## 协议

MIT
