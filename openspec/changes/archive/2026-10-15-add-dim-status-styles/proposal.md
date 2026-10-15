# Proposal

## Why

上一轮把消亡条目统一为红色加删除线后,红色样式不含变暗,消亡条目在终端里比正常条目还醒目;而「非活动条目应当 dim」是既有设计——已完成条目目前只有纯 dim,没有颜色语义。暗色主题下红/绿条目也更依赖 dim 才能压到背景层。

## What Changes

- 消亡条目(超龄/drop/erase 取走)样式在红色加删除线之外**追加 dim**,三种语境仍同源不变。
- 已完成条目样式从纯 dim 改为**绿色 + dim**,获得颜色语义(绿 = finished)。
- 两个主题字段(`cx.note.dropped`、`cx.note.done`)沿用现有登记名,仅改样式值;待办/进行中样式不变。
- 人读呈现规格同步:消亡与已完成的标识描述补「变暗」维度。

## Capabilities

### New Capabilities

(无)

### Modified Capabilities

- `cxnote`:「list 的平铺域块与折叠展示」「即将被清理的条目标记」「被删除条目以红色回显」三条需求的标识样式描述变化——消亡红色加删除线追加变暗,已完成由纯变暗改为绿色加变暗。

## Impact

- `packages/cxalio-studio-tools/cx_note/appenv.py`——`CX_NOTE_STYLES` 两字段样式值。
- `packages/cxalio-studio-tools/cx_note/components/list_view.py`——docstring 与注释中的样式语义描述(渲染逻辑本身走样式名,无需改动)。
- `openspec/specs/cxnote/spec.md`——三条需求的样式断言。
- `--json` 契约、ID 徽章、域标题、回显结构均不受影响。
- 版本迭代至 `1.4.1`（用户拍板，patch 档）：`cx_note/__init__.py` 的 `__version__` 与共享 `pyproject.toml` 同步。
