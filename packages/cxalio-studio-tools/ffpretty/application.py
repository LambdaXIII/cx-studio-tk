from collections.abc import Sequence
from datetime import datetime
import asyncio
import sys
from cx_studio.core.cx_time import CxTime
from cx_studio.ffmpeg import FFmpegArgumentsPreProcessor
from cx_tools.app import IApplication, SafeError
from cx_wealth.indexed_list_panel import IndexedListPanel
from packaging.tags import ios_platforms
from .appenv import appenv
from pathlib import Path
from cx_wealth import rich_types as r
from .transcoder import Transcoder
from .prober import Prober


class FFPrettyApp(IApplication):
    """
    FFPretty应用类 - FFmpeg的异步包装器，提供友好的用户界面

    这个类封装了FFmpeg的异步执行功能，包括：
    - 命令行参数解析和处理
    - 输入输出文件验证
    - 实时进度显示
    - 错误处理和用户反馈
    """

    def __init__(self, arguments: Sequence[str] | None = None):
        """
        初始化FFPretty应用

        Args:
            arguments: 命令行参数列表，如果为None则使用系统参数
        """
        super().__init__(arguments)
        self.arguments = []

        # 处理命令行参数，设置调试模式
        for a in self.sys_arguments:
            if a == "-d" or a == "--debug":
                # 启用调试模式
                appenv.debug_mode = True
            else:
                # 收集其他参数
                self.arguments.append(a)

        # 如果没有指定覆盖参数，默认使用 -n (不覆盖)
        if "-y" not in self.arguments and "-n" not in self.arguments:
            self.arguments.append("-n")

    def start(self):
        """
        启动应用

        初始化应用环境并记录开始时间
        """
        appenv.start()
        self.start_time = datetime.now()

    def stop(self):
        """
        停止应用

        清理应用环境，如果运行时间超过5秒则显示运行时间
        """
        appenv.stop()
        time_span = datetime.now() - self.start_time

        # 只有运行时间超过5秒才显示时间统计，避免频繁显示
        if time_span.total_seconds() > 5:
            appenv.say(
                "执行结束，用时[cx.number]{}[/]。".format(
                    CxTime.from_seconds(time_span.total_seconds()).pretty_string
                )
            )

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器退出处理

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息

        Returns:
            bool: 是否成功处理异常
        """
        result = False
        if exc_type is None:
            # 正常退出，没有异常
            pass
        elif issubclass(exc_type, SafeError):
            # 处理安全错误，显示错误信息
            appenv.say("[cx.error]错误：{}[/]".format(exc_val))
            result = True

        # 无论如何都要停止应用
        self.stop()
        return result

    def run_transcode(self):
        """运行转码过程"""
        with Transcoder(appenv.ffmpeg_executable) as transcoder:
            return asyncio.run(transcoder.run(self.arguments))

    def run_probe(self, files: list[Path]):
        prober = Prober()
        for x in files:
            prober.probe(x)

    def run(self) -> bool:
        # 验证参数
        if not appenv.ffmpeg_executable:
            raise SafeError("当前环境中未找到 [cx.filepath]ffmpeg[/] 可执行文件。")

        if not self.arguments:
            raise SafeError("未提供任何参数。")

        # 开始检查输入输出
        io_processor = FFmpegArgumentsPreProcessor(self.arguments)
        inputs = list(io_processor.iter_input_files())
        outputs = list(io_processor.iter_output_files())
        options = list(io_processor.iter_option_pairs())

        # 验证输入文件
        if (not inputs) and (not outputs):
            raise SafeError(
                "没有提供需要处理的文件，请按照 ffmpeg 的规则制定输入输出文件，或直接制定需要探测的文件。"
            )

        # 如果输入输出都有
        if len(inputs) > 0 and len(outputs) > 0:
            # 显示输入输出文件列表
            appenv.whisper(
                IndexedListPanel(inputs, title="输入文件"),
                IndexedListPanel(outputs, title="输出文件"),
            )
            self.run_transcode()
        elif not options:
            # 进入解析模式
            self.run_probe([Path(x) for x in inputs + outputs])
        else:
            appenv.say("[cx.error]参数无法解读。")
