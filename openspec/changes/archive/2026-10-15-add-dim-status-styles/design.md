# Design

## Context

`CX_NOTE_STYLES`（`cx_note/appenv.py`）登记了条目状态的主题字段，`make_entry_block`（`cx_note/components/list_view.py`）按消亡判定与状态选择样式名。上一轮改动后：消亡三语境共用 `cx.note.dropped`（`red strike`，无 dim），非消亡已完成用 `cx.note.done`（`dim`，无颜色），徽章对终态 dim。渲染逻辑只挂样式名，改样式值即可触达列表、回显、定位候选、清理报告全部场合。

## Goals / Non-Goals

**Goals:**
- 消亡样式在红+删除线之外追加变暗；已完成样式改为绿色+变暗。
- 两字段仍是唯二的非活动语义样式，待办/进行中不弱化的现状不变。

**Non-Goals:**
- 不改消亡判定逻辑、`taken` 透传、徽章着色规则。
- 不新增字段、不改字段名（`cx.note.dropped` / `cx.note.done` 沿用）。
- 不动 `--json` 契约与回显结构。

## Decisions

1. **样式值而非新字段**：在现有两个字段的值上加维（`red strike` → `red strike dim`；`dim` → `dim green`），替代增设「dim 变体字段」。理由：渲染侧已按语义（消亡/已完成）选字段，维度是样式的属性而非选择分支，拆字段只会多出一处无差别映射。
   - 备选「为每种状态各设 dim 与非 dim 字段」——被否：调用点没有非 dim 的使用场景，字段成对冗余。
2. **`dim` 放在样式串任意位置均可**：Rich 解析 `red strike dim` 与 `dim red strike` 等价，取与现有写法一致的词序。
3. **绿色选 `green` 而非 `bright green`**：dim 叠加后 bright 会回抬亮度，违背「非活动条目压到背景层」的意图。

## Risks / Trade-offs

- [低对比终端中 `dim green` 可读性下降] → dim 本就是设计意图（非活动弱化）；若个别终端不可读，调字段值即可，不动代码。
- [消亡红条目变暗后警示感减弱] → 「即将被清理」词形标记仍在，信息不依赖颜色单独承载。
