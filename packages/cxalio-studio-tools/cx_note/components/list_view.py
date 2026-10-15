"""列表渲染组件——纯函数层。

返回 renderable，由 application 用 `appenv.say()` 打印；不依赖 appenv。

容器设计：域标题行外置为裸路径字面（`cx.note.section` 样式），其下**每
条目一个**无框三列小 `Table`（`make_entry_block`）——ID 徽章（`width=4`
贴行首）/ 状态标号（自然宽，即将清理的条目在其后附提示）/ 内容
（`ratio=1`，显式 `overflow="fold"` 长行折行不截断）。三列 cell 均为
显式 style 的 `Text`（多行内容为 `Markdown`），规避 `say()` 默认高亮下
CxHighlighter 对 markup 字符串的重新染色。逐条目独立成表后，单条长内容
折行不再与同域其它条目争抢列宽。

展示语义（用户定案）：默认**折叠**——当前域条目全显，下级域只显示
标题行（相对当前域的字面 + 该域条目数）；`--full` 时下级域标题下接
各自条目块。当前域标题显示域名字（末段），根域显示 `GLOBAL`——当前
工作域非根时列表内不出现绝对路径。
"""

from cx_note.common import Entry, EntryStatus, ROOT_DOMAIN, canonical
from cx_note.i18n import _
from cx_wealthy import rich_types as r

# 状态标号——每条目行首
MARKER: dict[EntryStatus, str] = {
    EntryStatus.TODO: "[ ]",
    EntryStatus.PENDING: "[~]",
    EntryStatus.DONE: "[x]",
    EntryStatus.DROPPED: "[-]",
}

# 8 色高对比亮色调色板 + orange1（全部为 Rich ANSI 色名）；ID 字符按
# ord % len 定色——同一字符永远同一颜色，同 ID 内重复字符同色。
_PALETTE = [
    "bright_red",
    "bright_green",
    "bright_blue",
    "bright_cyan",
    "bright_magenta",
    "bright_yellow",
    "bright_white",
    "orange1",
]


def make_id_badge(eid: str, terminal: bool = False) -> r.Text:
    """把 4 位 ID 渲染为逐字符着色的徽章。

    必须返回显式 style 的 `Text` 而非 markup 字符串——`say()` 默认开启
    高亮，CxHighlighter 的 number/brackets 正则会重新染色干扰徽章。
    无背景色；`terminal` 为真时整体加 `dim`（终态条目的徽章随行转暗）。

    Args:
        eid: 条目 ID（小写 base36）。
        terminal: 条目是否处于终态（已完成或已取消）——真时附加 dim。

    Returns:
        逐 span 着色的 `Text`。
    """
    badge = r.Text()
    for ch in eid:
        fg = _PALETTE[ord(ch) % len(_PALETTE)]
        badge.append_text(r.Text(ch, style=f"{fg} dim" if terminal else fg))
    return badge


def make_entry_block(entry: Entry, expiring: bool = False) -> r.Table:
    """把单个条目渲染为无框三列小表（一条目一表）。

    三列顺序：ID 徽章（`width=4` 左对齐贴行首）/ 状态标号（自然宽）/
    内容（`ratio=1`，显式 `overflow="fold"`——长行折行而非 Rich 默认的
    ellipsis 截断）。终态弱化沿用既有决策：已取消的标号与内容转
    `cx.note.dropped`（dim + strike，多行内容整体随行转暗），已完成的
    标号与内容转 `cx.note.done` 且徽章 dim；进行中/待办不弱化。

    Args:
        entry: 待渲染条目（调用方已保证在正确域分组内）。
        expiring: 该条目是否即将被清理——真时标号后附清理提示。

    Returns:
        单条目的三列 `Table`。
    """
    is_terminal = entry.status in {EntryStatus.DONE, EntryStatus.DROPPED}
    terminal_style = (
        "cx.note.dropped"
        if entry.status is EntryStatus.DROPPED
        else "cx.note.done" if entry.status is EntryStatus.DONE else ""
    )
    marker = r.Text(MARKER[entry.status], style=terminal_style)
    if expiring:
        # 即将被清理的提示并入标号列，不另开列；不清理时该列只剩标号。
        marker.append_text(r.Text(" " + _("即将被清理"), style="cx.note.expiring"))
    if "\n" in entry.content:
        # 多行按 Markdown 渲染：已完成/进行中沿用「内容不置灰」的既有决策
        # （弱化由标号 + 徽章传达），已取消则整体 dim + strike。
        # 源行以「两空格 + 换行」拼接——Markdown 把单换行视为软换行会与
        # 下一行合并，行尾双空格才保留真实换行（经实验 3 源行渲 3 行）。
        # Rich 的 Markdown 只接受样式名，None 会在 Style.parse 抛错，
        # 故「不附加样式」必须走默认构造而非 style=None。
        joined = "  \n".join(entry.content.split("\n"))
        content: r.RenderableType = (
            r.Markdown(joined, style="cx.note.dropped")
            if entry.status is EntryStatus.DROPPED
            else r.Markdown(joined)
        )
    else:
        content = r.Text(entry.content, style=terminal_style)
    table = r.Table(box=None, show_header=False, padding=(0, 2, 0, 0), expand=True)
    table.add_column(width=4)
    table.add_column()
    table.add_column(ratio=1, overflow="fold")
    table.add_row(make_id_badge(entry.id, is_terminal), marker, content)
    return table


def _rel_label(domain: str, current: str) -> str:
    """返回下级域相对当前域的显示字面；不在子树内则返回绝对字面。

    按身份键（canonical）判断子树归属：`domain` 必须以
    `canonical(current) + "/"` 开头才算 `current` 的下级（带段边界，
    `/ab` 不算 `/a` 的下级）；不在子树内（跨域条目、非法输入）直接
    返回 `domain` 绝对字面，避免按长度硬切产出垃圾。canonical 即
    `lower()`，与字面同长，大小写不敏感场景切割仍正确（当前 `/ab`、
    下级 `/aB/c` → `/c`）。

    Args:
        domain: 下级域字面。
        current: 当前域字面。

    Returns:
        当前域为根域或 `domain` 不在其子树内 → `domain` 原样；否则
        截去当前域段并补 `/`。
    """
    if canonical(current) == ROOT_DOMAIN:
        return domain
    if not canonical(domain).startswith(canonical(current) + "/"):
        return domain
    return "/" + domain[len(canonical(current)) + 1 :]


def _head_label(domain: str) -> str:
    """返回当前域标题文本：域名字（末段），根域为固定标签 `GLOBAL`。

    当前工作域在列表首节只显示名字不显示全路径——深层域标题保持简短；
    根域（当前工作目录即 $HOME，或 `-g`）以 `GLOBAL` 为名。

    Args:
        domain: 当前域字面。

    Returns:
        根域 → `GLOBAL`；否则末段（`/a/b/c` → `c`）。
    """
    if canonical(domain) == ROOT_DOMAIN:
        return "GLOBAL"
    return domain.rsplit("/", 1)[-1]


def build_list_renderable(
    groups: list[tuple[str, list[Entry]]],
    current_domain: str,
    full: bool = False,
    expiring_ids: frozenset[str] = frozenset(),
    fill_current_empty: bool = True,
) -> r.Group:
    """把按域分组的条目组装为每域一小节的平铺列表。

    每节 = 标题行（`cx.note.section` 样式）+ 该域逐条目的
    `make_entry_block`；节间以空行分隔。显示规则（用户定案）：
    **当前工作域不是根时，列表内不出现绝对路径**——当前域标题只显示
    域名字（末段；根域显示固定标签 `GLOBAL`），不带数量；下级域标题
    显示相对当前域的字面并附 `(条目数)`——数量只数该域自身。

    Args:
        groups: `(域字面, 条目列表)` 序列，当前域组在前、其余按
            `canonical` 排序；组内按 `created_at` 升序。当前域无自身
            条目时 groups 可能只含下级域组。渲染器不排序，按到达顺序
            原样输出。
        current_domain: 当前域字面（标题名字与相对化基准）。
        full: 是否展开下级域条目——真时每个下级域标题下接条目块，
            假时折叠为仅标题行。
        expiring_ids: 即将被清理的条目 ID 集合——命中的条目块在标号
            后附清理提示。
        fill_current_empty: 当前域在 groups 中缺席时是否仍注入一个仅
            标题的当前域小节（列表用它标示所处位置；回显不想要时置
            False，此时从不注入）。

    Returns:
        各域小节与空行组成的 `Group`。
    """
    current_key = canonical(current_domain)
    # 当前域无自身条目但有下级域时，仍先给出当前域标题行（无条目块），
    # 让用户看到所在位置；`fill_current_empty=False`（回显）则跳过。
    blocks: list[tuple[str, list[Entry], bool]] = []
    if fill_current_empty and (not groups or canonical(groups[0][0]) != current_key):
        blocks.append((current_domain, [], True))
    for domain, entries in groups:
        blocks.append((domain, entries, canonical(domain) == current_key))

    lines: list[r.RenderableType] = []
    for index, (domain, entries, is_current) in enumerate(blocks):
        if index:
            lines.append(r.Text(""))
        shown = (
            _head_label(current_domain)
            if is_current
            else _rel_label(domain, current_domain)
        )
        title = r.Text(shown, style="cx.note.section")
        if not is_current:
            title.append_text(r.Text(f" ({len(entries)})", style="cx.note.hint"))
        lines.append(title)
        if entries and (is_current or full):
            for entry in entries:
                lines.append(make_entry_block(entry, expiring=entry.id in expiring_ids))
    return r.Group(*lines)
