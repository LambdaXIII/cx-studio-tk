# cx-wealth

**语言 / Languages**: [中文](README.md) | [English](README.en_US.md)

基于 [Rich](https://github.com/Textualize/rich) 的终端 UI 组件库，为 CLI 应用提供声明式帮助系统、标签渲染、详情面板和自适应布局等扩展。

## 安装

```bash
pip install cx-wealth
```

要求 Python >= 3.12, < 3.15。

## 组件

### WealthHelp — 声明式帮助系统 DSL

替代 argparse 的原生帮助输出。通过 `add_group` / `add_action` / `add_note` 构建结构化帮助信息，支持 Rich 样式的主题化输出。

```python
from cx_wealth import WealthHelp

help = WealthHelp(prog="myapp", description="My CLI tool")
help.add_action("--input", help="Input file path", nargs=1)
help.add_action("--output", help="Output file path", nargs=1)
help.add_group("Advanced", description="Advanced options")
help.add_note("See docs for more details.")
```

### WealthLabel — 可组合标签渲染

将实现了 `__rich_label__()` 协议的对象渲染为带 Markup 和样式的紧凑文本行。支持 crop、ellipsis、fold 三种溢出处理方式，可自定义分隔符。

```python
from cx_wealth import WealthLabelMixin

class MyItem(WealthLabelMixin):
    def __rich_label__(self):
        yield "[bold]MyItem[/]"
        yield "status: active"
        yield "[green]●[/]"
```

### WealthDetail / WealthDetailPanel — 详情展示

将实现了 `__rich_detail__()` 协议的对象渲染为两列键值表格。支持子面板嵌套和 Rich 样式。

### IndexedListPanel — 索引列表

在 Rich Panel 中显示带行号索引的列表。支持起始索引、最大行数控制（超出显示省略号）、边框样式自定义。

```python
from cx_wealth import IndexedListPanel

panel = IndexedListPanel(items=["a", "b", "c"], title="Files")
```

### DynamicColumns — 自适应多列布局

根据终端宽度自动计算列数和列宽，将对象集合渲染为多列布局。

## 链接

返回项目首页：[cx-studio-tk](../..)
