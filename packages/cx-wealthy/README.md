# cx-wealthy

基于 [Rich](https://github.com/Textualize/rich) 的终端结构化文档与 UI 组件库。

提供两种核心能力：

1. **结构化的文档系统** — 声明式复合树构建 + 主题化渲染，从帮助系统到任意分类文档都可使用
2. **双渲染协议** — `__rich_label__`(紧凑标签) + `__rich_detail__`(键值面板)，通过 mixin 让领域对象自身可渲染

## 安装

```bash
uv add cx-wealthy
```

要求 Python >= 3.12。

**唯一依赖**：`rich>=14.0.0`。不依赖 cx-studio 或其他包。

## 快速开始

### 标签渲染协议

让任意对象直接支持 Rich 渲染，输出紧凑标签行。

**继承 mixin（推荐，协议即渲染）：**

```python
from cx_wealthy import RichLabelMixin
from rich.console import Console

console = Console()

class Mission(RichLabelMixin):
    def __init__(self, name: str, target: str) -> None:
        self.name = name
        self.target = target

    def __rich_label__(self):
        yield "[bold]M[/]"
        yield self.name
        yield f"-> {self.target}"

console.print(Mission("encode", "output.mp4"))
# 输出： M encode -> output.mp4
```

**使用包装器（不愿继承时）：**

```python
from cx_wealthy import RichLabel

# 包装任意实现了 __rich_label__() 的对象
console.print(RichLabel(some_object, overflow="ellipsis"))
```

**自定义渲染（覆盖 mixin 默认实现）：**

```python
class Stream(RichLabelMixin):
    def __rich_label__(self):
        yield ...
    def __rich__(self):          # 覆盖默认，使用自定义渲染
        return custom_render(self)
```

### 详情渲染协议

将对象渲染为带键值对表格的面板，支持递归嵌套。

**继承 mixin：**

```python
from cx_wealthy import RichDetailMixin
from rich.console import Console

console = Console()

class Mission(RichDetailMixin):
    def __init__(self):
        self.source = "/path/to/input.mp4"
        self.target_format = "mp4"
        self.overwrite = False
        self.filter_chain = ["crop", "scale"]

    def __rich_detail__(self):
        yield "源文件", str(self.source)
        yield "目标格式", self.target_format
        yield "覆盖", self.overwrite, False   # (key, value, default) 三元组
        yield "过滤器链", self.filter_chain     # 自动渲染为 IndexedListPanel

console.print(Mission())
```

**`__rich_detail__` 支持的 yield 格式：**

| 元组形态 | 效果 |
|---|---|
| `(key, value)` | 显示 `key = value` |
| `(key, value, default)` | 当 `value == default` 时该行不显示（去重） |
| `(value,)` | 仅显示值，key 列为空 |
| `(key, *values)` | value 为列表 |

**使用包装器：**

```python
from cx_wealthy import WealthDetailPanel

console.print(WealthDetailPanel(mission, title="任务详情"))
```

### 结构化文档系统

通用文档树：`Node`（基类）→ `Group`（容器）+ `Note`（内容），通过 `WealthyDocument` 组织输出。

```python
from cx_wealthy import WealthyDocument, WealthyHelp, Action

# 通用结构化文档
doc = WealthyDocument(prog="myapp", description="工具说明")
doc.add_group("输入").add_note("支持格式：mp4, mkv, avi")
doc.add_group("输出").add_note("默认输出到当前目录")
console.print(doc)

# 帮助系统特化
help_doc = WealthyHelp(prog="myapp", description="CLI 工具说明")
help_doc.add_action("--input", metavar="FILE", description="输入文件路径")
help_doc.add_action("--output", metavar="FILE", description="输出文件路径")
help_doc.add_action("--verbose", description="详细输出")
help_doc.add_note("使用 --help 查看完整用法。")
console.print(help_doc)
```

`WealthyHelp` 自动渲染三部分：usage 行（选项按可选/位置分组排列）、参数详情表格、epilog 尾部。

### 索引列表面板

带行号索引的列表展示，支持截断。

```python
from cx_wealthy import IndexedListPanel

# 基本用法
console.print(IndexedListPanel(["a", "b", "c"], title="文件列表"))

# 不截断
console.print(IndexedListPanel(large_list, max_lines=None))

# 0-based 索引
console.print(IndexedListPanel(items, start_index=0))
```

### 固定列数布局

按最大列数平均分配宽度的多列布局。

```python
from cx_wealthy import MaxColumnsLayout

items = [renderable1, renderable2, renderable3, renderable4]
console.print(MaxColumnsLayout(items, max_columns=3, column_gap=2))
```

### 本地化教程渲染

按 locale 自动选择 Markdown 教程文件，加载并渲染为 Panel 包裹的 Markdown。

```python
from cx_wealthy import render_tutorial

# 自动检测 locale，优先加载 help.en_US.md，回退 help.md
console.print(render_tutorial(__package__, "help.md", title="教程"))
```

加载逻辑：先尝试 `<stem>.<locale><ext>`（如 `help.en_US.md`），失败则回退到基础文件名。不依赖 cx-studio，自行检测环境变量 `LANGUAGE` → `LC_ALL` → `LC_MESSAGES` → `LANG`。

### 主题预设

`cx.*` 命名空间的主题样式，供全局使用。

```python
from cx_wealthy.theme import default_theme, CX_STYLES

console = Console(theme=default_theme)
console.print("[cx.success]操作成功[/]")
console.print("[cx.error]操作失败[/]")
console.print("[cx.warning]注意[/]")
console.print("[cx.info]信息[/]")
```

可用样式：

| 样式 | 效果 |
|---|---|
| `cx.success` | 粗体绿色 |
| `cx.error` | 粗体红色 |
| `cx.warning` | 粗体黄色 |
| `cx.info` | 青色 |
| `cx.whisper` | 暗色 |
| `cx.number` | 青色 |

### Rich 类型便利出口

使用 `rich_types` 作为 Rich 高频类型的别名入口。

```python
from cx_wealthy import rich_types as r

table = r.Table(show_header=True)
table.add_column(r.Column("名称"))
r.Console().print(table)
```

内部使用（在 cx-wealthy 自身的模块中）始终使用 `from rich.xxx import Yyy` 真实路径，`rich_types` 仅对外。

## 模块索引

| 模块 | 内容 |
|---|---|
| `theme` | `cx.*` 主题样式预设 |
| `rich_types` | Rich 高频类型便利出口 |
| `label` | `RichLabelMixin` + `RichLabel` |
| `detail` | `RichDetailMixin` + `WealthDetailPanel` + `WealthDetailTable` |
| `document` | `Node` / `Group` / `Note` / `WealthyDocument` |
| `help` | `Action` / `WealthyHelp` |
| `indexed_list` | `IndexedListPanel` |
| `columns` | `MaxColumnsLayout` |
| `tutorial` | `render_tutorial()` |

## 开源协议

MIT
