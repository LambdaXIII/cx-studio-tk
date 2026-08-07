from cx_tools.app import IAppComponent, IAppEnvironment
from .appcontext import FFPrettyContext

from cx_studio import text as tt
from cx_wealthy import WealthyHelp
from ffpretty.i18n import _


class FFPrettyHelp(IAppComponent, WealthyHelp):
    def __init__(self, appenv: IAppEnvironment, context: FFPrettyContext):
        IAppComponent.__init__(self, appenv, context)
        self.appenv = appenv
        self.context = context
        WealthyHelp.__init__(self, prog="ffpretty")

        self.description = tt.auto_unwrap(
            _("""FFmpeg 友好前端。将 FFmpeg 参数直接转发给后台进程，并在前台
            输出美化过的转码信息和进度。附赠媒体文件的详细信息查询功能。
            """)
        )

        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

        # ── 转码模式 ──
        trans_group = self.add_group(
            _("转码模式"),
            _("ffpretty -i <输入文件> [FFmpeg 选项] <输出文件>"),
        )
        trans_group.add_action(
            "-y",
            name=_("强制覆盖"),
            detail=_(
                "覆盖已存在的输出文件。注意此选项由 ffpretty 自身处理，不会透传给 FFmpeg。"
            ),
        )
        trans_group.add_action(
            "-n",
            name=_("安全模式"),
            detail=_(
                "跳过已存在的输出文件（默认启用）。此选项由 ffpretty 自身处理，不会透传给 FFmpeg。"
            ),
        )

        # ── 查询模式 ──
        probe_group = self.add_group(
            _("查询模式"),
            _("ffpretty <媒体文件1> [<媒体文件2> …]"),
        )
        probe_group.add_action(
            "FILES",
            name=_("媒体文件"),
            metavar="FILE",
            nargs="*",
            detail=_(
                "输入媒体文件的路径，多个文件以空格分隔。查询结果会被缓存到数据库中，"
                "重复查询直接读取缓存。"
                "\n\n"
                "提示：也可以通过 -i 语法传入文件且不指定输出目标来进入查询模式，"
                "此时会忽略非文件选项。"
            ),
        )

        # ── 杂项 ──
        misc_group = self.add_group(_("杂项"))
        misc_group.add_action("-h", "--help", detail=_("显示此帮助信息"))
        misc_group.add_action(
            "-d", "--debug", detail=_("开启调试模式，显示内部诊断信息")
        )
        misc_group.add_action(
            "--pretend", detail=_("模拟运行，不调用 FFmpeg、不写文件")
        )
