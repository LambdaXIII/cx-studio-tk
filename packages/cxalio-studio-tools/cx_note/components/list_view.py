"""列表渲染组件——纯函数层。

返回 renderable，由 application 用 `appenv.say()` 打印；不依赖 appenv。

容器选择：初版用无框 Table 三列对齐，但长域字面的分节行在列宽分配下
必然断行割裂（预定回退条件命中），故按条目逐行渲染——分节标题行 +
每条目一行「标号 徽章 内容」，多行内容在头行下接 Markdown 块。
"""

from cx_note.common import Entry, EntryStatus, canonical
from cx_wealthy import rich_types as r

# 状态标号——每条目行首
MARKER: dict[EntryStatus, str] = {
    EntryStatus.TODO: "[ ]",
    EntryStatus.DOING: "[~]",
    EntryStatus.DONE: "[x]",
}

# 16 色循环调色板（全部为 Rich ANSI 标准色名）；ID 字符按 ord % 16 定色——
# 同一字符永远同一颜色，同 ID 内重复字符同色（已确认可接受）。
_PALETTE = [
    "red",
    "green1",
    "blue1",
    "magenta1",
    "cyan1",
    "yellow1",
    "orange1",
    "spring_green1",
    "violet",
    "steel_blue1",
    "pink1",
    "gold1",
    "pale_turquoise1",
    "purple",
    "chartreuse1",
    "deep_sky_blue1",
]


def make_id_badge(eid: str) -> r.Text:
    """把 4 位 ID 渲染为逐字符着色的徽章。

    必须返回显式 style 的 `Text` 而非 markup 字符串——`say()` 默认开启
    高亮，CxHighlighter 的 number/brackets 正则会重新染色干扰徽章。

    Args:
        eid: 条目 ID（小写 base36）。

    Returns:
        逐 span 着色的 `Text`。
    """
    badge = r.Text()
    for ch in eid:
        fg = _PALETTE[ord(ch) % len(_PALETTE)]
        badge.append_text(r.Text(ch, style=f"{fg} on grey15"))
    return badge


def _entry_head(entry: Entry) -> r.Text:
    """组装条目行的「标号 + 徽章 + 间隔」头段。"""
    head = r.Text()
    is_done = entry.status is EntryStatus.DONE
    head.append_text(
        r.Text(MARKER[entry.status], style="cx.note.done" if is_done else "")
    )
    head.append_text(r.Text("  "))
    head.append_text(make_id_badge(entry.id))
    head.append_text(r.Text("  "))
    return head


def build_list_renderable(
    groups: list[tuple[str, list[Entry]]], current_domain: str
) -> r.Group:
    """把按域分组的条目组装为逐行渲染的列表。

    Args:
        groups: `(域字面, 条目列表)` 序列，当前域组在前、其余按
            `canonical` 排序；组内按 `created_at` 升序。
        current_domain: 当前域字面——当前域分节行显示它，其余组显示
            各自首见字面。

    Returns:
        分节标题行与各条目行组成的 `Group`。
    """
    lines: list[r.RenderableType] = []
    for domain, entries in groups:
        shown = (
            current_domain if canonical(domain) == canonical(current_domain) else domain
        )
        lines.append(r.Text(f"█ {shown}", style="cx.note.section"))
        for entry in entries:
            is_done = entry.status is EntryStatus.DONE
            head = _entry_head(entry)
            if "\n" in entry.content:
                # 已完成多行仍按 Markdown 渲染（不置灰；置灰由标号+徽章列传达）
                lines.append(head)
                lines.append(r.Padding(r.Markdown(entry.content), (0, 0, 0, 4)))
            else:
                head.append_text(
                    r.Text(entry.content, style="cx.note.done" if is_done else "")
                )
                lines.append(head)
    return r.Group(*lines)
