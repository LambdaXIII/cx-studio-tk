English | [简体中文](README.md)

# cx-wealthy

A terminal structured document and UI component library built on [Rich](https://github.com/Textualize/rich).

Provides two rendering modes for domain objects and declarative structured document construction — no manual Table/Panel assembly, no inheriting Rich internal protocols.

## Installation

```bash
pip install cx-wealthy
```

To add to a uv project:

```bash
uv add cx-wealthy
```

## Core Concepts

### Label and Detail Rendering Protocols

cx-wealthy extends Rich with two rendering modes: `__rich_label__` (compact label, for inline summaries) and `__rich_detail__` (key-value panel, for structured details). Inheriting the corresponding mixin makes `console.print()` automatically render in that mode — no manual wrapping at the call site.

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
        yield "Name", self.name
        yield "Source", str(self.source)
        yield "Overwrite", self.overwrite, False        # 3-tuple: hidden when value == default

console.print(Mission("encode", "input.mp4"))
# Label output: M encode → input.mp4

console.print(WealthyDetailPanel(Mission("encode", "input.mp4")))
# Detail panel output, "Overwrite" row hidden because overwrite == False
```

When inheritance is not an option, use wrappers `RichLabel(obj)` / `WealthyDetailPanel(obj)` to render any object that implements the protocol.

**`__rich_detail__` yield formats:**

| Tuple form | Effect |
|---|---|
| `(key, value)` | Display `key = value` |
| `(key, value, default)` | Row hidden when `value == default` |
| `(value,)` | Value only, empty key column |
| `(key, *values)` | Value as list |

**Strings and markup**: `str` keys/values are displayed literally (no markup parsing); for markup formatting, yield `Text.from_markup(...)`.

`__rich_detail__` differs from Rich's native `__rich_repr__`: the latter is a debug repr (raw values + Pretty rendering), while the former is a presentation view (values can be pre-formatted, supports recursive sub-panel nesting, lists auto-rendered as `IndexedListPanel`).

### Declarative Document Construction

Build structured documents via a composite tree of `Node` → `Group` + `Note`, organized by `WealthyDocument` for rendering. The help system is a specialization layer — `WealthyHelp` extends `WealthyDocument`, adding `Action` nodes and usage/details rendering.

```python
from cx_wealthy import WealthyHelp

help = WealthyHelp(prog="myapp", description="A CLI tool")
help.add_action("--input", metavar="FILE", description="Input file path")
help.add_action("--output", metavar="FILE", description="Output file path")
help.add_action("--verbose", description="Verbose output")
help.add_note("Use --help for full usage.")
console.print(help)
```

`WealthyHelp` automatically renders a usage line (options grouped by optional/positional), a parameter details table, and an epilog.

`WealthyDocument` is not limited to help systems — any structured output with "groups + entries + notes" can be built with it.

## Utility Components

| Component | Purpose |
|---|---|
| `IndexedListPanel` | List panel with row index, supports truncation (`max_lines=None` for unlimited) |
| `MaxColumnsLayout` | Multi-column layout with a fixed maximum column count |
| `render_tutorial()` | Loads a Markdown tutorial file by locale and renders it as a Panel |

```python
from cx_wealthy import IndexedListPanel, MaxColumnsLayout, render_tutorial

console.print(IndexedListPanel(["a", "b", "c"], title="Files"))
console.print(MaxColumnsLayout(["one", "two", "three", "four"], max_columns=3))
console.print(render_tutorial(__package__, "help.md", title="Tutorial"))
```

## Theme Presets

Rich theme styles under the `cx.*` namespace.

```python
from cx_wealthy.theme import default_theme
from rich.console import Console

console = Console(theme=default_theme)
console.print("[cx.success]Success[/]")
console.print("[cx.error]Failed[/]")
```

| Style | Effect |
|---|---|
| `cx.success` | Bold green |
| `cx.error` | Bold red |
| `cx.warning` | Bold yellow |
| `cx.info` | Cyan |
| `cx.whisper` | Dim |
| `cx.number` | Cyan |

## Rich Types Convenience Export

```python
from cx_wealthy import rich_types as r

table = r.Table(show_header=True)
table.add_column(r.Column("Name"))
r.Console().print(table)
```

## Module Index

| Module | Exports |
|---|---|
| `label` | `RichLabelMixin` · `RichLabel` |
| `detail` | `RichDetailMixin` · `WealthyDetailTable` · `WealthyDetailPanel` |
| `document` | `Node` · `Group` · `Note` · `WealthyDocument` |
| `help` | `Action` · `WealthyHelp` |
| `indexed_list` | `IndexedListPanel` |
| `columns` | `MaxColumnsLayout` |
| `tutorial` | `render_tutorial` |
| `theme` | `CX_STYLES` · `HELP_STYLES` · `default_theme` |
| `rich_types` | Rich high-frequency type aliases |

## License

MIT
