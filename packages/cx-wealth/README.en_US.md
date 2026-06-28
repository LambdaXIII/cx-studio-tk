# cx-wealth

**语言 / Languages**: [中文](README.md) | [English](README.en_US.md)

A terminal UI component library built on [Rich](https://github.com/Textualize/rich), providing extensions for CLI applications including a declarative help system, label rendering, detail panels, and adaptive layouts.

## Installation

```bash
pip install cx-wealth
```

Requires Python >= 3.12, < 3.15.

## Components

### WealthHelp — Declarative Help System DSL

Replaces argparse's native help output. Build structured help information via `add_group` / `add_action` / `add_note`, with Rich-styled themed output.

```python
from cx_wealth import WealthHelp

help = WealthHelp(prog="myapp", description="My CLI tool")
help.add_action("--input", help="Input file path", nargs=1)
help.add_action("--output", help="Output file path", nargs=1)
help.add_group("Advanced", description="Advanced options")
help.add_note("See docs for more details.")
```

### WealthLabel — Composable Label Rendering

Renders objects implementing the `__rich_label__()` protocol as compact text lines with Markup and styling. Supports crop, ellipsis, and fold overflow modes, with customizable separators.

```python
from cx_wealth import WealthLabelMixin

class MyItem(WealthLabelMixin):
    def __rich_label__(self):
        yield "[bold]MyItem[/]"
        yield "status: active"
        yield "[green]●[/]"
```

### WealthDetail / WealthDetailPanel — Detail Display

Renders objects implementing the `__rich_detail__()` protocol as two-column key-value tables. Supports nested sub-panels and Rich styling.

### IndexedListPanel — Indexed List

Displays a list with line-number indices inside a Rich Panel. Supports configurable starting index, maximum line count (shows ellipsis when exceeded), and customizable border styles.

```python
from cx_wealth import IndexedListPanel

panel = IndexedListPanel(items=["a", "b", "c"], title="Files")
```

### DynamicColumns — Adaptive Multi-Column Layout

Automatically calculates column count and width based on terminal width, rendering a collection of objects in a multi-column layout.

## Links

Back to project root: [cx-studio-tk](../..)
