from cx_tools.i18n import _

from cx_studio.i18n import load_localized_text

from cx_studio import text as tt
from cx_wealthy import WealthyHelp
from cx_wealthy import rich_types as r
from .appenv import appenv


class AppHelp(WealthyHelp):
    def __init__(self) -> None:
        super().__init__(prog="hostskeeper")

        # 直接运行（无子命令）—— 显示帮助
        self.add_group(
            _("直接运行"),
            detail=_("不带任何子命令运行时，显示此帮助信息。"),
        )

        # 子命令
        commands = self.add_group(_("子命令"))

        list_cmd = commands.add_command("list", detail=_("列出所有配置文件。"))
        list_cmd.add_action(
            "-s",
            "--search",
            name=_("搜索模式"),
            metavar="SEARCH_PATTERN",
            detail=_("搜索模式，支持 glob 形式的通配符，智能搜索配置文件的多种信息。"),
        )

        show_cmd = commands.add_command("show", detail=_("显示指定配置文件的内容。"))
        show_cmd.add_action(
            "PROFILE_ID",
            name=_("配置文件ID"),
            metavar="PROFILE_ID",
            detail=_("配置文件的ID。"),
        )

        edit_cmd = commands.add_command("edit", detail=_("编辑指定配置文件。"))
        edit_cmd.add_action(
            "PROFILE_ID",
            name=_("配置文件ID"),
            metavar="PROFILE_ID",
            detail=_("配置文件的ID。"),
        )

        update_cmd = commands.add_command(
            "update", detail=_("按照所有激活的配置文件更新hosts。")
        )
        update_cmd.add_action(
            "--target",
            "--to",
            "-t",
            name=_("目标文件"),
            metavar="TARGET_HOSTS",
            detail=_("指定目标 hosts 文件，默认值为系统 hosts 文件。"),
        )
        update_cmd.add_action(
            "--skip-flush",
            name=_("跳过刷新"),
            detail=_("更新 hosts 后跳过 DNS 缓存刷新，仅输出平台对应的手动命令提示。"),
        )

        new_cmd = commands.add_command("new", detail=_("创建新的配置文件。"))
        new_cmd.add_action(
            "PROFILE_ID",
            name=_("配置文件ID"),
            metavar="PROFILE_ID",
            detail=_("配置文件的ID。"),
        )

        # 杂项（全局选项）—— 移至末尾
        misc_opts = self.add_group(_("杂项"))
        misc_opts.add_action("-h", "--help", detail=_("显示此帮助信息"))
        misc_opts.add_action(
            "--tutorial", "--full-help", detail=_("显示完整的教程内容")
        )
        misc_opts.add_action(
            "-d", "--debug", detail=_("开启调试模式以观察更多的后台信息")
        )
        misc_opts.add_action(
            "-p",
            "--pretend",
            detail=_("启用[bold blue]模拟运行模式[/]，不会进行任何文件操作。"),
        )

        misc_opts.add_note(
            r.Text.from_markup(
                f"[default dim italic]{_('建议通过完整帮助信息学习更多使用技巧。')}[/]"
            )
        )

        self.description = tt.auto_unwrap(
            _("""本工具通过一系列配置文件自动编写操作系统的 hosts 文件。
        配置文件可通过 [u]list[/] [u]show[/] [u]edit[/] 等命令进行管理。
        执行 [u]update[/] 命令后，hosts 文件将被自动更新。
        当然，编辑 hosts 文件需要以管理员权限运行。""")
        )

        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

    @staticmethod
    def show_help() -> None:
        appenv.say(AppHelp())

    @staticmethod
    def show_full_help() -> None:
        assert __package__ is not None, "AppHelp must be imported as part of a package"
        md = load_localized_text(__package__, "help.md")
        content = r.Markdown(md, style="default")
        panel = r.Panel(
            content,
            title=_("Hosts Keeper 教程"),
            width=90,
            style="bright_black",
            title_align="left",
        )
        appenv.say(r.Align.center(panel))
