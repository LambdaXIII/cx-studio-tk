"""Jpegger 帮助系统。"""

from cx_studio import text as tt
from cx_studio.i18n import load_localized_text
from cx_tools.app import IAppComponent, IAppEnvironment
from cx_wealthy import WealthyHelp
from cx_wealthy import rich_types as r
from jpegger.i18n import _

from .appcontext import JpeggerContext, _COLOR_SPACE_CHOICES
from .components.format_database import FormatDB


class JpeggerHelp(IAppComponent, WealthyHelp):
    """Jpegger 的中文帮助文档。"""

    def __init__(self, appenv: IAppEnvironment, context: JpeggerContext):
        """使用 WealthyHelp DSL 构建帮助内容。"""
        IAppComponent.__init__(self, appenv, context)
        self.appenv = appenv
        self.context = context
        WealthyHelp.__init__(self, prog="jpegger")
        self.description = tt.auto_unwrap(
            _("""Jpegger是一个简单的批量转换图片的命令行工具。

            使用选项可以简单地控制输出图片的尺寸、编码质量和色彩空间。
            本工具旨在快速地进行简单的批量处理，所以暂不提供更高级的客制化功能。
            """)
        )
        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

        basic_opts = self.add_group(_("基本选项"))
        basic_opts.add_action(
            "inputs", nargs="*", metavar="FILE", detail=_("需要转码的文件")
        )
        basic_opts.add_action(
            "-f",
            "--format",
            metavar="FORMAT",
            detail=_(
                "指定输出格式（名称或扩展名，不区分大小写），默认沿用原始格式。可用：{formats}"
            ).format(formats=", ".join(FormatDB.formats())),
        )
        basic_opts.add_action(
            "-q",
            "--quality",
            metavar="QUALITY",
            detail=_("指定输出质量，默认使用内置的常用质量设置"),
        )
        basic_opts.add_action(
            "-o", "--output", metavar="DIR", detail=_("输出目录，默认为当前目录")
        )

        image_controls = self.add_group(_("图片处理"), _("对图像进行处理"))
        image_controls.add_action(
            "--scale", metavar="FACTOR", detail=_("按比例缩放图片的尺寸")
        )
        image_controls.add_action(
            "-s",
            "--size",
            metavar="WIDTHxHEIGHT",
            detail=_("指定图片的尺寸，接受包含两个数字的表达式"),
        )
        image_controls.add_action(
            "--width",
            metavar="WIDTH",
            detail=_("指定图片的宽度，如果未指定高度则保持原始图像比例"),
        )
        image_controls.add_action(
            "--height",
            metavar="HEIGHT",
            detail=_("指定图片的高度，如果未指定宽度则保持原始图像比例"),
        )
        image_controls.add_action(
            "-c",
            "--color-space",
            metavar="SPACE",
            detail=_("设置目标色彩空间，可用：{choices}").format(
                choices=", ".join(_COLOR_SPACE_CHOICES)
            ),
        )

        process_control = self.add_group(_("其它选项"))
        process_control.add_action(
            "--force-overwrite",
            "-y",
            detail=_("强制覆盖已存在的文件，未设置时将会跳过"),
        )
        process_control.add_action("--debug", detail=_("显示调试信息"))
        process_control.add_action("-h", "--help", detail=_("显示帮助信息"))
        process_control.add_action(
            "--tutorial",
            "--full-help",
            detail=_("显示完整的教程内容"),
        )

    def show_help(self) -> None:
        """在控制台打印简要帮助。"""
        self.appenv.console.print(self)

    def show_full_help(self) -> None:
        """在控制台打印完整教程（help.md）。"""
        assert __package__ is not None, "JpeggerHelp 必须作为包的一部分导入"
        md = load_localized_text(__package__, "help.md")
        content = r.Markdown(md, style="default")
        panel = r.Panel(
            content,
            title=_("Jpegger 教程"),
            title_align="left",
            style="bright_black",
            width=90,
        )
        self.appenv.console.print(r.Align.center(panel))
