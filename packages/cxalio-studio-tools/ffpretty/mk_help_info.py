from cx_studio import text as tt
from cx_wealth import WealthHelp


class MKHelp(WealthHelp):
    def __init__(self, **kwargs):
        super().__init__(prog="ffpretty", **kwargs)

        self.description = tt.auto_unwrap(
            """本工具直接转发 FFmpeg 的选项，并在后台调用，
            同时在前台输出美化过的转码信息。
            """
        )

        self.epilog = (
            "[link https://github.com/LambdaXIII/cx-studio-tk]Cxalio Studio Tools[/]"
        )

        trans_group = self.add_group("转码模式", "直接使用ffmpeg的选项即可开始转码。")
        probe_group = self.add_group(
            "查询模式", "直接输入多个媒体文件，查询文件的信息而不进行转码。"
        )
