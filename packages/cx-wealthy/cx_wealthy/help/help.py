"""帮助系统特化文档：WealthyHelp。"""

from __future__ import annotations

from collections.abc import Generator
from typing import Literal, override

from rich.align import Align
from rich.console import Group as RichGroup, RenderableType
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..document.document import WealthyDocument
from ..document.node import Node
from ..document.note import Note
from .action import Action
from .help_group import HelpGroup

__all__ = ["WealthyHelp"]


class WealthyHelp(WealthyDocument):
    """帮助系统特化文档。

    继承 :class:`WealthyDocument` 的通用文档能力，增加 ``add_action()``、
    ``render_usage()``、``render_details()``、``render_epilog()``。

    主题透明：组件内 ``style="cx.help.*"`` 等样式名是约定，由调用方
    通过 ``Console(theme=...)`` 决定是否应用 :data:`cx_wealthy.default_theme`。
    """

    def __init__(
        self,
        *,
        prog: str | None = None,
        description: RenderableType | None = None,
        epilog: RenderableType | None = None,
    ) -> None:
        """
        Args:
            prog: 程序名；None 时在 render 阶段延迟取 ``sys.argv[0]``。
            description: 文档描述。
            epilog: 尾部内容。
        """
        super().__init__(prog=prog, description=description, epilog=epilog)

    @override
    def add_group(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> HelpGroup:
        """添加子 Group，返回 :class:`HelpGroup` 以支持 add_action / add_command。

        覆盖 WealthyDocument.add_group：在帮助场景下，子 Group 分组 Action 或
        组织子命令区块，故返回 HelpGroup 提供便利方法。
        """
        return HelpGroup(name=name, description=description, parent=self.root)

    def add_action(
        self,
        *flags: str,
        name: str | None = None,
        description: str | None = None,
        metavar: str | None = None,
        nargs: int | Literal["?", "+", "*", "**"] | None = None,
        optional: bool | None = None,
        prefix_chars: str = "-",
    ) -> Action:
        """创建 :class:`Action` 并添加到 root，返回该 ``Action``。"""
        return Action(
            *flags,
            name=name,
            description=description,
            metavar=metavar,
            nargs=nargs,
            optional=optional,
            parent=self.root,
            prefix_chars=prefix_chars,
        )

    def add_command(
        self,
        *keywords: str,
        name: str | None = None,
        description: str | None = None,
    ) -> HelpGroup:
        """创建顶层命令 HelpGroup（commands 非空）并添加到 root。

        返回的 HelpGroup 可继续 add_action（专有参数）、add_command（嵌套子命令）。
        """
        return HelpGroup(
            *keywords, name=name, description=description, parent=self.root
        )

    @override
    def render(self) -> Generator[RenderableType, None, None]:
        """yield usage、details、epilog（非空）。"""
        yield self.render_usage()
        yield self.render_details()
        epilog = self.render_epilog()
        if epilog is not None:
            yield epilog

    def render_usage(self) -> RenderableType:
        """渲染用法区域。

        所有 usage 行放入同一个双列 Table（prog 左列 | usage 右列），保证对齐一致。
        首行 prog 列填 prog_text，后续行（子命令详版）左列留空——右列自然在
        prog 列宽度之后开始，与首行右列对齐。单行时循环为空，行为等价。
        """
        prog_text = Text(self.prog + " ", style="cx.help.usage.prog")
        # root 传空 Text——各行的 prog 由 Table 左列统一提供，不在行文本中重复
        usage_lines = self._render_node_usage(self.root, Text())

        table = Table(box=None, show_header=False, padding=(0, 0))
        table.add_column(style="cx.help.usage.prog", justify="left", no_wrap=True)
        table.add_column(ratio=1)

        # 首行：prog | 简版总览（prog 末尾有空格，作列间分隔）
        table.add_row(prog_text, usage_lines[0])

        # 后续行：每个子命令的详版（prog 列留空，列宽含末尾空格，右列自然对齐）
        for line in usage_lines[1:]:
            table.add_row("", line)

        # 给 Table 加左 padding，与下方 description 的 2 格左 padding 对齐
        parts: list[RenderableType] = [Padding(table, pad=(0, 0, 0, 2))]

        if self.description is not None:
            if isinstance(self.description, str):
                desc_renderable = Text.from_markup(self.description)
            else:
                desc_renderable = self.description
            parts.append(Padding(desc_renderable, pad=(1, 0, 0, 2)))

        content = RichGroup(*parts) if len(parts) > 1 else parts[0]

        return Panel(
            content,
            title=Text("用法", style="cx.help.usage.title"),
            border_style="cx.help.details.box",
        )

    def _render_node_usage(self, node: Node, path: Text) -> list[Text]:
        """递归渲染某节点的 usage 行。
        算法（每层相同）：
        1. 分类 node 的直接子节点：
           - Action → local_args
           - HelpGroup（is_command=True）→ sub_commands
           - HelpGroup（is_command=False）→ 内含 Action 归入 local_args，
             内含 HelpGroup（is_command=True）归入 sub_commands，
             内含 HelpGroup（is_command=False）递归展开
        2. 简版行：path + sub_commands pipe 列表 + local_args（optional→positional 排序）
        3. 详版行：每个 sub_command 递归，path 追加命令关键词

        Args:
            node: 当前节点（root 或某个 HelpGroup）
            path: 命令路径前缀 Text（root 时为 prog，子命令时为 prog + cmd keywords）

        Returns:
            usage 行列表（叶子命令只一行，有子命令的节点多行）
        """
        lines: list[Text] = []

        # 分类子节点
        direct_actions: list[Action] = []
        sub_commands: list[HelpGroup] = []
        for child in node.iter_children():
            if isinstance(child, Action):
                # Action → 当前层级的 local_args
                direct_actions.append(child)
            elif isinstance(child, HelpGroup):
                if child.is_command:
                    # commands 非空 → 参与 pipe 列表拼接
                    sub_commands.append(child)
                else:
                    # 非命令容器：内含 Action 归入 local_args，内含命令归入 sub_commands
                    for grandchild in child.iter_children():
                        if isinstance(grandchild, Action):
                            direct_actions.append(grandchild)
                        elif (
                            isinstance(grandchild, HelpGroup) and grandchild.is_command
                        ):
                            sub_commands.append(grandchild)
                        elif (
                            isinstance(grandchild, HelpGroup)
                            and not grandchild.is_command
                        ):
                            sub_commands.extend(grandchild.iter_commands())

        # local_args 按 optional → positional 桶排序
        optional_args = [
            a for a in direct_actions if a.is_optional() and not a.is_positional()
        ]
        positional_args = [
            a for a in direct_actions if a.is_positional() and not a.is_optional()
        ]
        other_args = [
            a
            for a in direct_actions
            if a not in optional_args and a not in positional_args
        ]

        # 简版行：path + sub_commands pipe 列表 + local_args
        # 子命令在前，参数在后——符合 CLI 惯例（git/docker/kubectl）。
        # path 为空时不加前导空格——render_usage() 统一添加列间距。
        line = Text()
        line.append_text(path)
        if sub_commands:
            if path.plain:
                line.append(" ")
            cmd_text = self._render_command_list(sub_commands)
            line.append_text(cmd_text)
        for action in optional_args + positional_args + other_args:
            line.append(" ")
            line.append_text(action.render_usage())
        lines.append(line)

        # 详版行：每个子命令递归。
        # render_usage() 传空 path（prog 由 Table 左列提供），故 root 层 path.plain
        # 为 falsy，不加 leading space——避免详版行右列中出现多余前导空白。
        # 嵌套递归时 path 已含上级命令关键词，加空格分隔。
        for cmd in sub_commands:
            cmd_path = Text()
            cmd_path.append_text(path)
            if path.plain:
                cmd_path.append(" ")
            cmd_path.append(cmd.commands[0], style="cx.help.usage.command")
            sub_lines = self._render_node_usage(cmd, cmd_path)
            lines.extend(sub_lines)

        return lines

    def _render_command_list(self, commands: list[HelpGroup]) -> Text:
        """渲染子命令 pipe 列表（如 list|show|edit|update|help）。

        每个 HelpGroup 的命令关键词用 ``|`` 分隔，同一命令的别名也用
        ``|`` 分隔。按 CLI 惯例，子命令列表不加方括号（子命令通常是必需的）。
        若调用方需要表示可选子命令，可在 description 中说明。
        """
        result = Text()
        for i, cmd in enumerate(commands):
            if i:
                result.append("|", style="cx.help.usage.bracket")
            # 命令关键词，别名用 | 分隔
            for j, kw in enumerate(cmd.commands):
                if j:
                    result.append("|", style="cx.help.usage.bracket")
                result.append(kw, style="cx.help.usage.command")
        return result

    def render_details(self) -> RenderableType:
        """渲染参数详情，按 Group 分组。

        处理顺序：
        1. root 下未分组的 Action（逐行详情）
        2. root 下的非命令 HelpGroup（组标题 + 组内 Action 详情）
        3. root 下的命令 HelpGroup（子命令区块，递归展开每个命令的详情）
        """

        all_actions = [node for node in self.root.walk() if isinstance(node, Action)]
        if not all_actions:
            return Text("")

        parts: list[RenderableType] = []

        # 1. 未分组 Action
        ungrouped_actions: list[Action] = []
        for child in self.root.iter_children():
            if isinstance(child, Action):
                ungrouped_actions.append(child)

        for action in ungrouped_actions:
            parts.append(action.render_details())

        # 2. 非命令 HelpGroup（参数分组）
        for child in self.root.iter_children():
            if not isinstance(child, HelpGroup) or child.is_command:
                continue
            group_parts: list[RenderableType] = []

            if child.name:
                title_text = Text(child.name, style="cx.help.group.title")
                title_text.stylize("bold")
                group_parts.append(title_text)

            if child.description:
                group_parts.append(
                    Padding(
                        Text(child.description, style="cx.help.group.description"),
                        pad=(0, 0, 0, 2),
                    )
                )

            group_actions: list[Action] = []
            for group_child in child.iter_children():
                if isinstance(group_child, Action):
                    group_actions.append(group_child)

            if group_actions:
                action_lines = [a.render_details() for a in group_actions]
                group_parts.append(Padding(RichGroup(*action_lines), pad=(0, 0, 0, 4)))

            # 非命令容器内含的子命令
            for group_child in child.iter_children():
                if isinstance(group_child, HelpGroup):
                    sub_details = self._render_command_group_details(group_child)
                    if sub_details is not None:
                        group_parts.append(Padding(sub_details, pad=(0, 0, 0, 4)))

            if group_parts:
                if parts:
                    parts.append(Text(""))
                parts.append(RichGroup(*group_parts))

        # 3. 命令 HelpGroup（子命令区块）
        for child in self.root.iter_children():
            if isinstance(child, HelpGroup) and child.is_command:
                cmd_details = self._render_command_group_details(child)
                if cmd_details is not None:
                    if parts:
                        parts.append(Text(""))
                    parts.append(cmd_details)

        content = RichGroup(*parts) if len(parts) > 1 else parts[0]

        return Panel(
            content,
            title="参数详情",
            border_style="cx.help.details.box",
        )

    def _render_command_group_details(
        self, cmd_group: HelpGroup
    ) -> RenderableType | None:
        """渲染命令群的详情区块。

        若 cmd_group 是纯容器（commands 为空）：
            - 用 cmd_group.name 作为区块标题（如"子命令"）
            - 列出其下每个命令的详情
        若 cmd_group 是命令本身（commands 非空）：
            - 用命令关键词作为标题
            - 列出该命令的专有参数详情
            - 若有嵌套子命令，递归渲染

        每个命令的详情行格式：
            命令关键词          命令描述
                专有参数1        参数描述
                专有参数2        参数描述
        """
        parts: list[RenderableType] = []

        if cmd_group.is_command:
            # 命令本身：渲染关键词 + 描述 + 专有参数 + 嵌套子命令
            cmd_parts: list[RenderableType] = []

            # 命令关键词和描述
            cmd_label = Text()
            for j, kw in enumerate(cmd_group.commands):
                if j:
                    cmd_label.append(", ")
                cmd_label.append(kw, style="cx.help.usage.command")
            if cmd_group.description:
                cmd_label.append(
                    f"  {cmd_group.description}",
                    style="cx.help.details.description",
                )
            cmd_parts.append(cmd_label)

            # 该命令的专有参数（Action）
            cmd_actions: list[Action] = []
            for child in cmd_group.iter_children():
                if isinstance(child, Action):
                    cmd_actions.append(child)
            if cmd_actions:
                action_lines = [a.render_details() for a in cmd_actions]
                cmd_parts.append(Padding(RichGroup(*action_lines), pad=(0, 0, 0, 4)))

            # 嵌套子命令递归
            for child in cmd_group.iter_children():
                if isinstance(child, HelpGroup) and child.is_command:
                    nested = self._render_command_group_details(child)
                    if nested is not None:
                        cmd_parts.append(Padding(nested, pad=(0, 0, 0, 2)))

            parts.append(RichGroup(*cmd_parts))
        else:
            # 纯容器：标题 + 其下每个命令的详情
            if cmd_group.name:
                title_text = Text(cmd_group.name, style="cx.help.group.title")
                title_text.stylize("bold")
                parts.append(title_text)

            if cmd_group.description:
                parts.append(
                    Padding(
                        Text(
                            cmd_group.description,
                            style="cx.help.group.description",
                        ),
                        pad=(0, 0, 0, 2),
                    )
                )

            # 容器下的每个命令
            for child in cmd_group.iter_children():
                if isinstance(child, HelpGroup) and child.is_command:
                    sub_details = self._render_command_group_details(child)
                    if sub_details is not None:
                        parts.append(Padding(sub_details, pad=(0, 0, 0, 4)))

        if not parts:
            return None
        if len(parts) == 1:
            return parts[0]
        return RichGroup(*parts)

    def render_epilog(self) -> RenderableType | None:
        """渲染尾部内容或 notes；为空时返回 None。"""
        parts: list[RenderableType] = []

        if self.epilog is not None:
            if isinstance(self.epilog, str):
                epilog_text = Text.from_markup(self.epilog, style="cx.help.epilog")
                parts.append(Align.right(epilog_text))
            else:
                parts.append(self.epilog)

        for node in self.root.walk():
            if isinstance(node, Note):
                parts.append(node.render())

        if not parts:
            return None
        if len(parts) == 1:
            return parts[0]
        return RichGroup(*parts)
