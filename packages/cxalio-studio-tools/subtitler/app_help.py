"""Subtitler 帮助组件——`-h` 分组帮助与 `--tutorial` 完整教程。

结构与其余工具的 `app_help.py` 同构：`SubtitlerHelp` 多重继承
`IAppComponent`（取 appenv/context）与 `WealthyHelp`（帮助 DSL），
分组覆盖转换动作、支持的格式与杂项选项。
"""

from cx_studio import text as tt
from cx_studio.i18n import load_localized_text
from cx_tools.app import IAppComponent, IAppEnvironment
from cx_wealthy import WealthyHelp
from cx_wealthy import rich_types as r

from .appcontext import SubtitlerContext
from .i18n import _


class SubtitlerHelp(IAppComponent, WealthyHelp):
    """subtitler 分组帮助文档。

    Args:
        appenv: 应用环境实例。
        context: 命令行上下文。
    """

    def __init__(self, appenv: IAppEnvironment, context: SubtitlerContext) -> None:
        IAppComponent.__init__(self, appenv, context)
        self.appenv = appenv
        self.context = context
        WealthyHelp.__init__(self, prog="subtitler")

        # 转换
        convert = self.add_group(_("转换"))
        convert.add_action(
            "INPUT",
            name=_("输入文件"),
            metavar="INPUT",
            detail=_(
                "待转换的字幕文件；格式按扩展名识别，支持 .srt / .ttml / "
                ".xml / .dfxp / .csv。"
            ),
        )
        convert.add_action(
            "OUTPUT",
            name=_("输出文件"),
            metavar="OUTPUT",
            detail=_(
                "转换目标文件；格式按扩展名识别，未识别的扩展名报错中止；"
                "目标已存在时报错且不覆盖。"
            ),
        )

        # 杂项
        misc = self.add_group(_("杂项"))
        misc.add_action("-d", "--debug", detail=_("开启 debug 模式。"))
        misc.add_action("-h", "--help", detail=_("显示此分组帮助。"))
        misc.add_action("--tutorial", detail=_("显示完整教程。"))

        self.add_note(
            r.Text.from_markup(
                _(
                    "支持的格式：SRT（[u].srt[/]）、TTML（[u].ttml[/] / "
                    "[u].xml[/] / [u].dfxp[/]）、CSV（[u].csv[/]）。三者都可作"
                    "源与目标，可任意互转，同格式往返也允许。"
                )
            )
        )

        self.add_note(
            r.Text.from_markup(
                _(
                    "工具只搬运字幕模型，不编辑内容：读出全部条目，按时间组织，"
                    "再以目标格式写出。目标格式不允许交叠时自动拆分为多个文件，"
                    "命名为「目标文件名 + [u].part<k>[/]」（k 从 1 起）；"
                    "写出前一次性预检全部目标路径，任一已存在即中止、零输出。"
                )
            )
        )

        self.description = tt.auto_unwrap(
            _(
                """subtitler —— 字幕格式互转工具。
        支持 SRT / TTML / CSV 互转：读入 [u]INPUT[/]、写出 [u]OUTPUT[/]，格式按扩展名识别。
        只做格式搬运，不改写、不修剪、不重排字幕内容。运行 [u]subtitler --tutorial[/] 学习完整用法。"""
            )
        )

        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

    def show_help(self) -> None:
        """打印分组帮助。"""
        self.appenv.console.print(self)

    def show_full_help(self) -> None:
        """以面板打印完整教程（本地化 help.md）。"""
        assert __package__ is not None, "SubtitlerHelp 必须作为包的一部分被导入"
        md = load_localized_text(__package__, "help.md")
        content = r.Markdown(md, style="default")
        panel = r.Panel(
            content,
            title=_("Subtitler 教程"),
            width=90,
            style="bright_black",
            title_align="left",
        )
        self.appenv.console.print(r.Align.center(panel))
