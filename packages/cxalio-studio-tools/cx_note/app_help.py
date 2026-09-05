"""CxNote 帮助组件——`-h` 分组帮助与 `--tutorial` 完整教程。

结构与其余 5 工具的 `app_help.py` 同构（模板：hosts_keeper）：
`CxNoteHelp` 多重继承 `IAppComponent`（取 appenv/context）与
`WealthyHelp`（帮助 DSL），分组覆盖 7 个动词与全局选项。
"""

from cx_note.i18n import _

from cx_studio import text as tt
from cx_studio.i18n import load_localized_text
from cx_wealthy import WealthyHelp
from cx_wealthy import rich_types as r
from cx_tools.app import IAppComponent, IAppEnvironment

from .appcontext import CxNoteContext


class CxNoteHelp(IAppComponent, WealthyHelp):
    """cxnote 分组帮助文档。

    Args:
        appenv: 应用环境实例。
        context: 命令行上下文。
    """

    def __init__(self, appenv: IAppEnvironment, context: CxNoteContext) -> None:
        IAppComponent.__init__(self, appenv, context)
        self.appenv = appenv
        self.context = context
        WealthyHelp.__init__(self, prog="cxnote")

        def add_target(command) -> None:
            """给转移/删除类命令挂 TARGET 位置参数。"""
            command.add_action(
                "TARGET",
                name=_("ID 或文本片段"),
                metavar="ID|TEXT",
                detail=_(
                    "目标条目：4 位 ID 全库精确匹配；或文本片段"
                    "（当前域及下级域内匹配，须唯一命中）。"
                ),
            )

        # 快速记录
        add_cmd = self.add_group(_("快速记录")).add_command(
            "add",
            detail=_("记录一条内容到当前工作域；同域已有完全相同内容时不重复记录。"),
        )
        add_cmd.add_action(
            "TEXT",
            name=_("条目内容"),
            metavar="TEXT",
            detail=_(
                '条目文本；字面 [u]\\n[/] 转换为换行，如 [u]add "买菜\\n做饭"[/]。'
            ),
        )

        # 查看列表
        list_cmd = self.add_group(_("查看列表")).add_command(
            "list", detail=_("按域分组显示条目；不带动词运行时默认执行。")
        )
        list_cmd.add_action(
            "--full", detail=_("展开下级域的条目；默认下级域只显示标题行。")
        )

        # 状态流转
        transit = self.add_group(_("状态流转"))
        finish_cmd = transit.add_command("finish", detail=_("把条目标记为已完成。"))
        add_target(finish_cmd)
        pend_cmd = transit.add_command("pend", detail=_("把条目转入进行中。"))
        add_target(pend_cmd)
        reset_cmd = transit.add_command("reset", detail=_("把条目重置为待办。"))
        add_target(reset_cmd)

        # 删除
        remove = self.add_group(_("删除"))
        erase_cmd = remove.add_command("erase", detail=_("删除单条条目。"))
        add_target(erase_cmd)
        remove.add_command(
            "clear",
            detail=_("清空当前工作域的直属条目（不含子域），交互确认一次。"),
        )

        # 域选项
        domain_opts = self.add_group(_("域选项"))
        domain_opts.add_action(
            "-p",
            "--path",
            name=_("域字面"),
            metavar="DOMAIN",
            detail=_(
                "指定工作域：以 [u]/[/] 开头为绝对域，否则相对当前域；"
                "对所有动词生效。"
            ),
        )
        domain_opts.add_action("-g", "--global", detail=_("在根域操作。"))

        # 输出选项
        out_opts = self.add_group(_("输出选项"))
        out_opts.add_action(
            "--json", detail=_("向 stdout 输出纯净 JSON，跳过标题与一切装饰。")
        )
        out_opts.add_action(
            "--full", detail=_("展开下级域；同时扩大 [u]list --json[/] 的输出范围。")
        )
        out_opts.add_action("-d", "--debug", detail=_("开启 debug 模式。"))

        # 杂项
        misc = self.add_group(_("杂项"))
        misc.add_action("-h", "--help", detail=_("显示此分组帮助。"))
        misc.add_action("--tutorial", detail=_("显示完整教程。"))

        self.add_note(
            r.Text.from_markup(
                _(
                    "定位规则：[u]ID[/] 全库精确定位；[u]文本片段[/] 限可见域"
                    "（当前域 + 下级域）且须唯一命中；[u]-p[/] 改变所有动词的工作域。"
                )
            )
        )

        self.description = tt.auto_unwrap(_("""cxnote —— 终端里的快速便签。
        以 [u]add[/] 记录、[u]list[/] 查看、[u]finish[/] [u]pend[/] [u]reset[/] 流转状态、
        [u]erase[/] [u]clear[/] 删除。运行 [u]cxnote --tutorial[/] 学习完整用法。"""))

        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

    def show_help(self) -> None:
        """打印分组帮助。"""
        self.appenv.console.print(self)

    def show_full_help(self) -> None:
        """以面板打印完整教程（本地化 help.md）。"""
        assert __package__ is not None, "CxNoteHelp 必须作为包的一部分被导入"
        md = load_localized_text(__package__, "help.md")
        content = r.Markdown(md, style="default")
        panel = r.Panel(
            content,
            title=_("CxNote 教程"),
            width=90,
            style="bright_black",
            title_align="left",
        )
        self.appenv.console.print(r.Align.center(panel))
