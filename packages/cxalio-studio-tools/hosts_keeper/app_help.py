from cx_tools.i18n import _

from cx_studio.i18n import load_localized_text

from cx_studio import text as tt
from cx_wealth import WealthHelp
from cx_wealth import rich_types as r


class AppHelp(WealthHelp):
    def __init__(self) -> None:
        super().__init__(prog="hostskeeper")

        opt_group = self.add_group(_("命令和参数"))

        opt_group.add_action(
            "COMMAND",
            name=_("命令"),
            nargs="?",
            optional=True,
            metavar="list|show|edit|update|help",
            description=_("""\
要执行的操作，可选值为：
 - [u]list[/]：列出所有配置文件。
 - [u]show[/]：显示当前配置文件的内容。
 - [u]edit[/]：编辑当前配置文件。
 - [u]update[/]：按照所有激活的配置文件更新hosts。
 - [u]help[/]：显示帮助信息。"""),
        )

        opt_group.add_action(
            "PROFILE_ID",
            name=_("配置文件ID"),
            optional=True,
            metavar="PROFILE_ID",
            description=_("配置文件的ID，在 show 和 edit 命令中必须要指定。"),
        )

        opt_group.add_action(
            "--search-pattern",
            "-s",
            name=_("搜索模式"),
            optional=True,
            metavar="SEARCH_PATTERN",
            description=_(
                "如果在 list 中指定了搜索模式，将只会显示符合条件的配置文件。搜索模式支持 glob 形式的通配符，并会智能搜索配置文件的多种信息以找到符合条件的目标。"
            ),
        )

        opt_group.add_action(
            "--target",
            "--to",
            "-t",
            name=_("目标文件"),
            optional=True,
            metavar="TARGET_HOSTS",
            description=_("指定目标 hosts 文件，默认值为系统 hosts 文件。"),
        )
        opt_group.add_action(
            "--skip-flush",
            name=_("跳过刷新"),
            optional=True,
            description=_(
                "更新 hosts 后跳过 DNS 缓存刷新，仅输出平台对应的手动命令提示。"
            ),
        )

        misc_opts = self.add_group(_("杂项"))
        misc_opts.add_action("-h", "--help", description=_("显示此帮助信息"))
        misc_opts.add_action(
            "--tutorial", "--full-help", description=_("显示完整的教程内容")
        )
        misc_opts.add_action(
            "-d", "--debug", description=_("开启调试模式以观察更多的后台信息")
        )
        misc_opts.add_action(
            "-p",
            "--pretend",
            description=_("启用[bold blue]模拟运行模式[/]，不会进行任何文件操作。"),
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
    def show_help(console: r.Console) -> None:
        console.print(AppHelp())

    @staticmethod
    def show_full_help(console: r.Console) -> None:
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
        console.print(r.Align.center(panel))
