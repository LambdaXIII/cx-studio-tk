import importlib.resources

from cx_studio import text as tt
from cx_wealth import WealthHelp
from cx_wealth import rich_types as r


class MKHelp(WealthHelp):
    def __init__(self):
        super().__init__(prog="mediakiller")

        trans_opts = self.add_group("转码选项", "控制转码操作的选项")
        trans_opts.add_action(
            "inputs",
            nargs="+",
            metavar="FILE",
            description="指定（多个）需要处理的文件，包括[u]预设文件[/]和[u]源文件路径[/]。",
        )
        trans_opts.add_action(
            "-o",
            "--output",
            metavar="DIR",
            description="指定目标文件夹，如果不指定则默认为当前工作目录。",
        )
        trans_opts.add_action(
            "--sort",
            metavar="source|preset|target|x",
            description=tt.auto_unwrap(
                """设置任务的排序模式，在执行任务之前将会按照指定的模式进行排序。
            四种模式分别为[u]按源文件路径排序[/]、[u]按预设排序[/]、[u]按目标文件路径排序[/]、[u]按输入顺序排序[/]。"""
            ),
        )

        trans_opts.add_action(
            "-j",
            "--jobs" "--max-workers",
            metavar="NUM",
            description=tt.auto_unwrap(
                """
                设置并行工作进程的数量，默认为 1 。
                不建议设置大于 2 的数值，除非你知道你在干什么。
                """
            ),
        )

        trans_opts.add_action(
            "-y",
            "--overwrite",
            description="启用[red bold]强制覆盖模式[/]后，将忽略配置文件中定义的覆盖选项。",
        )
        trans_opts.add_action(
            "-n",
            "--no-overwrite",
            description="启用[green bold]安全模式[/]之后，将忽略一切覆盖选项，无论如何也不会覆盖目标文件。",
        )

        basic_opts = self.add_group("其它操作", "运行除了转码之外的操作")
        basic_opts.add_action(
            "-g",
            "--generate",
            metavar="PRESET",
            description="以示例内容生成预设文件。[uu]示例文件不可直接运行！[/]",
            nargs="+",
        )
        basic_opts.add_action(
            "-s",
            "--save",
            metavar="FILE",
            description="保存转码任务为脚本文件，将不再主动进行转码操作。",
        )
        basic_opts.add_action(
            "-c",
            "--continue",
            description="加载上次的[u]所有[/]转码任务并重新执行。\n如果想要继续运行未完成的任务，建议附加 -n 选项。",
        )

        misc_opts = self.add_group("杂项")
        misc_opts.add_action("-h", "--help", description="显示此帮助信息")
        misc_opts.add_action(
            "--tutorial", "--full-help", description="显示完整的教程内容"
        )
        misc_opts.add_action(
            "-d", "--debug", description="开启调试模式以观察更多的后台信息"
        )
        misc_opts.add_action(
            "-p",
            "--pretend",
            description="启用[bold blue]模拟运行模式[/]，不会进行任何文件操作。",
        )

        self.description = tt.auto_unwrap(
            """本工具从用户提供的输入中识别[u]预设文件[/]和[u]媒体源文件[/]，
            并基于它们生成一系列任务，并调用 FFmpeg 进行转码。"""
        )

        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

    @staticmethod
    def show_help(console: r.Console):
        console.print(MKHelp())

    @staticmethod
    def show_full_help(console: r.Console):
        md = importlib.resources.read_text("media_killer", "help.md")
        content = r.Markdown(md, style="default")
        panel = r.Panel(
            content,
            title="Media Killer 教程",
            width=90,
            style="bright_black",
            title_align="left",
        )
        console.print(r.Align.center(panel))
