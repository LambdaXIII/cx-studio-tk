# cx-wealthy

**语言 / Languages**: [中文](README.md) | English (TODO)

基于 [Rich](https://github.com/Textualize/rich) 的终端结构化文档与 UI 组件库。

本包是 `cx-wealth` 的继任者，从头重新设计，修复了旧版的协议语义混淆、抽象覆盖缺口、封装泄漏等问题。

## 设计文档

完整的背景、设计意图、决策依据与功能规格见 [DESIGN.md](DESIGN.md)。

## 安装

```bash
uv add cx-wealthy
```

要求 Python >= 3.12, < 3.15。

## 主要模块

| 模块 | 能力 |
|---|---|
| `theme` | `cx.*` 命名空间主题样式预设（success / error / warning / info 等）。 |
| `rich_types` | 对外的 Rich 高频类型便利出口。 |
| `label` | 紧凑标签协议 `RichLabelMixin` + `RichLabel` 包装器。 |
| `detail` | 详情键值面板协议 `RichDetailMixin` + `WealthDetailPanel` / `WealthDetailTable`。 |
| `document` | 通用结构化文档核心：`Node` / `Group` / `Note` / `WealthyDocument`。 |
| `help` | 帮助系统特化层：`Action` / `WealthyHelp`。 |
| `indexed_list` | 带索引的列表面板 `IndexedListPanel`。 |
| `columns` | 固定最大列数布局 `MaxColumnsLayout`。 |
| `tutorial` | 本地化教程渲染 `render_tutorial()`。 |

## 基本用法

继承 mixin，让对象直接可被 Rich 渲染：

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
```

使用声明式帮助系统：

```python
from cx_wealthy.help import WealthyHelp, Action

help_doc = (
    WealthyHelp(title="mytool")
    .add_group("输入")
    .add_action(Action(flags=["-i", "--input"], metavar="PATH", help="输入文件路径"))
    .add_group("输出")
    .add_action(Action(flags=["-o", "--output"], metavar="PATH", help="输出文件路径"))
)

help_doc.render()
```

## 与 cx-wealth 的关系

`cx-wealthy` 是 `cx-wealth` 的继任者，二者在迁移期内共存于 monorepo。
`cx-wealthy` 从头重新设计，修复了旧版在协议语义、抽象覆盖、封装泄漏等方面的问题；
`cxalio-studio-tools` 将逐步从 `cx-wealth` 切换到 `cx-wealthy`。
迁移完成后，`cx-wealth` 将从 workspace 移除并停止维护。

## 返回项目首页

[cx-studio-tk](../..)
