from cx_wealth import RichHelpInfo


class MKHelpInfo(RichHelpInfo):
    def __init__(self):
        super().__init__("mediakiller")
        basic_group = self.add_group("基本功能")
        basic_group.add_action("-h", "--help", description="显示帮助信息")
        basic_group.add_action("-v", "--version", description="显示版本信息")
        basic_group.add_action("-d", "--debug", description="显示调试信息")
        basic_group.add_action("-p", "--pretend", description="pretend mode")
        basic_group.add_action("-f", "--force", description="强制覆盖输出文件")
        transcoding_group = self.add_group("转码功能")
        transcoding_group.add_action("-i", "--input", description="输入文件")
        transcoding_group.add_action("-o", "--output", description="输出文件")
        transcoding_group.add_action("-s", "--sort", description="排序模式")
        transcoding_group.add_action("-c", "--continue", description="继续转码")
