# Design

## Context

cxnote 的人读样式集中在两处：`cx_note/appenv.py` 的 `CX_NOTE_STYLES` 主题表（`cx.note.dropped` = `dim strike`、`cx.note.expiring` = `yellow`、`cx.note.done` = `dim`）与 `cx_note/components/list_view.py` 的 `make_entry_block`（按条目状态与 `expiring` 参数选样式）。动机见 proposal.md - Why。

当前三种「消亡」语境的视觉不一致：

- 已取消（dropped）：标号与内容 `dim + strike`；
- 即将被清理（expiring）：本体按状态弱化（done 为 dim），仅提示词为黄色 `cx.note.expiring`；
- 被删除（erase/clear 回显、清理报告）：按取走前状态渲染，无任何标识。

## Goals / Non-Goals

**Goals:**

- 三种消亡语境统一为同一种红色 + 删除线视觉，同一语义样式字段。
- 变更收敛在主题表与条目块渲染函数内部：判定「是否消亡」的输入仍是渲染函数已有的参数面（条目状态 + expiring 标志）或一次简单的调用点透传，不引入新的计算或数据流。

**Non-Goals:**

- 不改 `--json` 契约（`expiring` 键不变）。
- 不改已完成（非超龄）条目的 dim 样式、待办/进行中样式、域标题样式。
- 不新增主题字段（用户裁定）。
- 不改条目块结构（三列、折行、词形标记「即将被清理」均保留）。

## Decisions

### 1. 单一样式字段 `cx.note.dropped`，定义改为 `red strike`；删除 `cx.note.expiring`

三种消亡语境共用 `cx.note.dropped` 一个字段（用户裁定「不要设置多个重复的样式」）。`cx.note.expiring` 的唯一用途（提示词「即将被清理」着色）并入统一字段，故整字段删除。不新增字段。

被否方案：新增 `cx.note.danger` 之类字段区分「弱化」与「危险」——用户明确不要多个样式字段；且三语境视觉本来就该一致。

### 2. 判定收敛在 `make_entry_block` 内部

「消亡」判定为 `status is DROPPED or expiring or taken`，在 `make_entry_block` 内计算，命中时标号、内容（含多行 Markdown 整体）、提示词统一挂 `cx.note.dropped`。`cx.note.done`（dim）仅对非超龄的已完成条目生效——超龄的 done 条目由 expiring 分支覆盖为红色。

多行内容的 Markdown 已有先例（dropped 整体挂样式），沿用同一路径，无新模式。

### 3. `taken` 标志由调用点透传，不新增判定逻辑

被删除条目（erase/clear 回显、清理报告）的「已取走」身份只有调用方知道，渲染函数无从计算。方案：`make_entry_block` 与 `build_list_renderable` 各加一个 `taken: bool = False` 形参；`application.py` 中 `_echo_changed`（erase/clear 路径）与 `_finalize` 清理报告调用点传 `taken=True`。这是把已有的调用点事实透传给渲染函数，不是在其它部分增加样式逻辑——样式决策仍全部在 `make_entry_block` 内。

被否方案：给 `Entry` 加「已取走」状态或在回显前复制条目改状态——污染数据模型，且条目已离开工作集，状态不真实。

### 4. 超龄条目在回显中也走红色

`_echo_changed` 已接收 `expiring_ids`，转移/edit 回显中命中 expiring 的条目自然由判定 2 覆盖为红色，无需额外改动。

## Risks / Trade-offs

- `cx.note.expiring` 字段删除后，若仓库其它处引用会断裂——已核查仅 `list_view.py` 使用（`appenv.py` 定义 + 一处着色），无外泄。
- 红色 + 删除线在非暗色终端下对比度可能偏弱：与现有 dim 方案同类风险，不新增处置。
- 多行 Markdown 整体挂样式会把 strike 传播到全部渲染行——与现行 dropped 行为一致，属预期。
