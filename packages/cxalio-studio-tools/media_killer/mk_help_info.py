from cx_wealth import WealthHelpInfomation


class MKHelpInfo(WealthHelpInfomation):
    def __init__(self):
        super().__init__(prog="mediakiller")

        trans_opts = self.add_group("转码选项")
        trans_opts.add_action(
            "inputs", nargs="+", metavar="FILE", description="输入文件"
        )
        trans_opts.add_action(
            "-o", "--output", metavar="DIR", description="指定输出目录"
        )
        trans_opts.add_action(
            "--sort",
            metavar="source|preset|target|x",
            description="设置任务的排序模式",
        )

        trans_opts.add_action("-y", "--overwrite", description="强制覆盖已存在的文件")
        trans_opts.add_action("-n", "--no-overwrite", description="不覆盖已存在的文件")

        basic_opts = self.add_group("其它操作")
        basic_opts.add_action(
            "-g", "--generate", metavar="PRESET", description="生成预设文件", nargs="+"
        )
        basic_opts.add_action(
            "-s", "--save", metavar="FILE", description="保存转码任务为脚本文件"
        )
        basic_opts.add_action(
            "-c", "--continue", description="重新加载上次的转码任务并进行操作"
        )

        misc_opts = self.add_group("杂项")
        misc_opts.add_action("-h", "--help", description="显示帮助信息")
        misc_opts.add_action(
            "--tutorial", "--full-help", description="显示完整的帮助信息"
        )
        misc_opts.add_action("--debug", description="开启调试模式")
        misc_opts.add_action("--pretend", description="启用模拟运行")
