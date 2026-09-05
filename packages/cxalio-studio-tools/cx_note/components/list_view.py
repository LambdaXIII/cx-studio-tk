"""列表渲染组件——纯函数层。

返回 renderable，由 application 用 `appenv.say()` 打印；不依赖 appenv。

容器设计（第 2 轮样式迭代）：域标题行外置为裸路径字面
（`cx.note.section` 样式），其下接**每域一个**无框三列小 `Table`——
标号 / 内容 / ID 徽章各占一列：标号列自然宽，内容列 `ratio=1` 撑满，
徽章列 `width=4` 右对齐贴行尾。三列 cell 均为显式 style 的 `Text`
（多行内容为 `Markdown`），规避 `say()` 默认高亮下 CxHighlighter 对
markup 字符串的重新染色。初版「分节行割裂列宽」的根因（长域字面占据
Table 内行）随标题行外置而消失。

展示语义（用户定案）：默认**折叠**——当前域条目全显，下级域只显示
标题行（相对当前域的字面 + 该域条目数）；`--full` 时下级域标题下接
各自条目表。当前域标题显示域名字（末段），根域显示 `GLOBAL`——当前
工作域非根时列表内不出现绝对路径。
"""

from cx_note.common import Entry, EntryStatus, ROOT_DOMAIN, canonical
from cx_wealthy import rich_types as r

# 状态标号——每条目行首
MARKER: dict[EntryStatus, str] = {
    EntryStatus.TODO: "[ ]",
    EntryStatus.DOING: "[~]",
    EntryStatus.DONE: "[x]",
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


def make_id_badge(eid: str, done: bool = False) -> r.Text:
    """把 4 位 ID 渲染为逐字符着色的徽章。

    必须返回显式 style 的 `Text` 而非 markup 字符串——`say()` 默认开启
    高亮，CxHighlighter 的 number/brackets 正则会重新染色干扰徽章。
    无背景色；`done` 为真时整体加 `dim`（已完成条目的徽章随行转暗）。

    Args:
        eid: 条目 ID（小写 base36）。
        done: 条目是否已完成——真时附加 dim。

    Returns:
        逐 span 着色的 `Text`。
    """
    badge = r.Text()
    for ch in eid:
        fg = _PALETTE[ord(ch) % len(_PALETTE)]
        badge.append_text(r.Text(ch, style=f"{fg} dim" if done else fg))
    return badge


def _domain_table(entries: list[Entry]) -> r.Table:
    """把一个域的条目渲染为无框三列小表。

    Args:
        entries: 该域条目（调用方已按创建时间升序）。

    Returns:
        三列 `Table`——标号自然宽、内容 `ratio=1`、徽章 `width=4`。
    """
    table = r.Table(box=None, show_header=False, padding=(0, 2, 0, 0), expand=True)
    table.add_column()
    table.add_column(ratio=1)
    table.add_column(justify="right", width=4)
    for entry in entries:
        is_done = entry.status is EntryStatus.DONE
        marker = r.Text(MARKER[entry.status], style="cx.note.done" if is_done else "")
        if "\n" in entry.content:
            # 已完成多行仍按 Markdown 渲染（内容不置灰；置灰由标号+徽章传达）
            content: r.RenderableType = r.Markdown(entry.content)
        else:
            content = r.Text(entry.content, style="cx.note.done" if is_done else "")
        table.add_row(marker, content, make_id_badge(entry.id, is_done))
    return table


def _rel_label(domain: str, current: str) -> str:
    """返回下级域相对当前域的显示字面。

    按身份键（canonical）长度切割：canonical 即 `lower()`，与字面同长，
    大小写不敏感场景切割仍正确（当前 `/ab`、下级 `/aB/c` → `/c`）。

    Args:
        domain: 下级域字面。
        current: 当前域字面。

    Returns:
        当前域为根域时返回 `domain` 原样；否则截去当前域段并补 `/`。
    """
    if canonical(current) == ROOT_DOMAIN:
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
) -> r.Group:
    """把按域分组的条目组装为每域一小节的平铺列表。

    每节 = 标题行（`cx.note.section` 样式）+ 可选条目小表；节间以空行
    分隔。显示规则（用户定案）：**当前工作域不是根时，列表内不出现
    绝对路径**——当前域标题只显示域名字（末段；根域显示固定标签
    `GLOBAL`），不带数量；下级域标题显示相对当前域的字面并附
    `(条目数)`——数量只数该域自身。

    Args:
        groups: `(域字面, 条目列表)` 序列，当前域组在前、其余按
            `canonical` 排序；组内按 `created_at` 升序。当前域无自身
            条目时 groups 可能只含下级域组。
        current_domain: 当前域字面（标题名字与相对化基准）。
        full: 是否展开下级域条目——真时每个下级域标题下接条目表，
            假时折叠为仅标题行。

    Returns:
        各域小节与空行组成的 `Group`。
    """
    current_key = canonical(current_domain)
    # 当前域无自身条目但有下级域时，仍先给出当前域标题行（无表），
    # 让用户看到所在位置。
    blocks: list[tuple[str, list[Entry], bool]] = []
    if not groups or canonical(groups[0][0]) != current_key:
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
            lines.append(_domain_table(entries))
    return r.Group(*lines)
