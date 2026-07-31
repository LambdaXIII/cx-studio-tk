"""media_killer 帮助信息。

使用 ``cx_wealthy.WealthyHelp`` 声明式构建帮助文档，
通过 ``cx_studio.i18n.load_localized_text`` 加载本地化教程。
"""

from cx_tools.app import IAppComponent, IAppEnvironment
from media_killer.i18n import _
from .appcontext import AppContext
from cx_studio.i18n import load_localized_text

from cx_studio import text as tt
from cx_wealthy import WealthyHelp
from cx_wealthy import rich_types as r

__all__ = ["MediaKillerHelp"]


class MediaKillerHelp(IAppComponent, WealthyHelp):
    """media_killer 帮助信息。

    继承 :class:`WealthyHelp`，使用 ``add_group`` / ``add_action``
    声明式构建命令行帮助文档。
    """

    def __init__(self, appenv: IAppEnvironment, context: "AppContext") -> None:
        IAppComponent.__init__(self, appenv, context)
        self.appenv = appenv
        self.context = context
        WealthyHelp.__init__(self, prog="mediakiller")

        self.description = tt.auto_unwrap(
            _("""本工具从用户提供的输入中识别[u]预设文件[/]和[u]媒体源文件[/]，
                并基于它们生成一系列任务，调用 FFmpeg 进行转码。""")
        )

        # ── 输入 ──
        inputs = self.add_group(_("输入"), _("预设文件与源文件的混合输入"))
        inputs.add_action(
            "inputs",
            nargs="+",
            metavar="FILE",
            detail=_(
                "指定（多个）需要处理的文件，包括[u]预设文件[/]和[u]源文件路径[/]。"
            ),
        )

        # ── 转码选项 ──
        trans_opts = self.add_group(_("转码选项"), _("控制转码操作的选项"))
        trans_opts.add_action(
            "-o",
            "--output",
            metavar="DIR",
            detail=_("指定目标文件夹，覆盖预设中的目标目录。"),
        )
        trans_opts.add_action(
            "--sort",
            metavar="source|preset|target|x",
            detail=tt.auto_unwrap(
                _(
                    """设置任务的排序模式。
                    四种模式分别为[u]按源文件路径[/]、[u]按预设[/]、[u]按目标文件路径[/]、[u]按输入顺序（默认）[/]。"""
                )
            ),
        )
        trans_opts.add_action(
            "-j",
            "--jobs",
            "--max-workers",
            metavar="NUM",
            detail=tt.auto_unwrap(_("""设置并行工作进程的数量，默认为 1。
                    不建议设置大于 2 的数值，除非你知道你在干什么。""")),
        )
        trans_opts.add_action(
            "-y",
            "--overwrite",
            detail=_("启用[cx.error]强制覆盖模式[/]，忽略预设文件中的覆盖选项。"),
        )
        trans_opts.add_action(
            "-n",
            "--no-overwrite",
            detail=_("启用[cx.success]安全模式[/]，无论如何也不覆盖已有目标文件。"),
        )

        # ── 其它操作 ──
        other_ops = self.add_group(_("其它操作"), _("除转码之外的辅助操作"))
        other_ops.add_action(
            "-g",
            "--generate",
            metavar="PRESET",
            nargs="+",
            detail=_("以示例内容生成预设文件。[cx.warning]示例文件不可直接运行！[/]"),
        )
        other_ops.add_action(
            "-s",
            "--save",
            metavar="FILE",
            detail=_("将转码任务保存为脚本文件，不执行转码。"),
        )
        other_ops.add_action(
            "-c",
            "--continue",
            detail=_(
                "加载上次的[u]所有[/]转码任务并叠加到本次任务中。\n建议附加 -n 选项以避免覆盖已完成的输出。"
            ),
        )

        # ── 杂项 ──
        misc = self.add_group(_("杂项"))
        misc.add_action("-h", "--help", detail=_("显示此帮助信息"))
        misc.add_action(
            "--tutorial",
            "--full-help",
            detail=_("显示完整的教程内容"),
        )
        misc.add_action("-d", "--debug", detail=_("开启调试模式以显示更多后台信息"))
        misc.add_action(
            "-p",
            "--pretend",
            detail=_("启用[cx.info]模拟运行模式[/]，不执行任何文件操作。"),
        )

        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

    def show_help(self) -> None:
        """显示简要帮助。"""
        self.appenv.console.print(self)

    def show_full_help(self) -> None:
        """显示完整教程。"""
        md = load_localized_text("media_killer", "help.md")
        content = r.Markdown(md, style="default")
        panel = r.Panel(
            content,
            title="Media Killer 教程",
            width=90,
            style="cx.debug",
            title_align="left",
        )
        self.appenv.console.print(r.Align.center(panel))
