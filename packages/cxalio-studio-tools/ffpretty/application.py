import asyncio
from collections.abc import Iterable, Sequence
from datetime import datetime
import itertools
import sys
from cx_studio.core.cx_time import CxTime
from cx_studio.ffmpeg import FFmpegAsync
from cx_studio.ffmpeg.cx_ff_infos import FFmpegCodingInfo
from cx_tools.app import IApplication, SafeError
from cx_wealth.indexed_list_panel import IndexedListPanel
from .appenv import appenv
from pathlib import Path
from cx_wealth import rich_types as r


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

        # 初始化FFmpeg异步执行器
        self.ffmpeg = FFmpegAsync(appenv.ffmpeg_executable)
        self.start_time: datetime

        # 任务描述文本，用于进度显示
        self._task_description: str = ""

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

    def input_files(self) -> Iterable[str]:
        """
        提取输入文件列表

        解析命令行参数，找到所有标记为输入的文件

        Yields:
            str: 输入文件路径
        """
        input_marked = False
        for a in self.arguments:
            if a == "-i":
                # 标记下一个参数为输入文件
                input_marked = True
            elif input_marked:
                # 当前参数是输入文件
                yield a
                input_marked = False

    def output_files(self) -> Iterable[str]:
        """
        提取输出文件列表

        解析命令行参数，找到所有输出文件（不包括输入文件）

        Yields:
            str: 输出文件路径
        """
        prev_key = None
        for a in self.arguments:
            if a.startswith("-"):
                # 当前参数是选项键
                prev_key = a
                continue

            # 如果参数包含点号且不是输入参数，则认为是输出文件
            if "." in a and prev_key != "-i":
                yield a

    async def _random_task_description(self):
        """
        异步循环显示任务描述

        用于进度显示，在输入和输出文件名之间循环切换，
        让用户知道当前正在处理哪个文件

        Raises:
            asyncio.CancelledError: 当任务被取消时正常退出
        """
        # 获取所有输入和输出文件名
        input_files = [Path(x).name for x in self.input_files()]
        output_files = [Path(x).name for x in self.output_files()]

        # 无限循环显示文件名
        for name in itertools.cycle(input_files + output_files):
            try:
                self._task_description = name
                await asyncio.sleep(2)  # 每2秒切换一次
            except asyncio.CancelledError:
                # 任务被取消时正常退出
                break

    async def execute(self, args: Iterable[str]):
        """
        执行FFmpeg命令的主要异步方法

        创建进度显示，设置状态监听器，并发执行FFmpeg任务和描述循环任务

        Args:
            args: FFmpeg命令参数

        Returns:
            bool: 执行结果
        """
        # 创建进度任务
        task_id = appenv.progress.add_task("[green]正在开始...[/]", total=None)

        # 统计输入输出文件数量用于显示
        m, n = len(list(self.input_files())), len(list(self.output_files()))
        sumary = f"[blue][{m}->{n}][/]"

        # 设置FFmpeg状态更新监听器
        @self.ffmpeg.on("status_updated")
        def on_status_updated(status: FFmpegCodingInfo):
            """FFmpeg状态更新回调函数"""
            current = status.current_time.total_seconds
            total = status.total_time.total_seconds if status.total_time else None

            # 格式化速度显示
            speed = "[bright_black][{:.2f}x][/]".format(status.current_speed)
            desc = f"{sumary}{speed}[green]{self._task_description}[/]"

            # 更新进度显示
            appenv.progress.update(
                task_id,
                completed=current,
                total=total,
                description=desc,
            )

        # 并发执行FFmpeg任务和描述循环任务
        ff_task = asyncio.create_task(self.ffmpeg.execute(args))
        desc_task = asyncio.create_task(self._random_task_description())

        # 等待FFmpeg任务完成，同时监听退出事件
        while not ff_task.done():
            await asyncio.sleep(0.01)
            if appenv.wanna_quit_event.is_set():
                # 用户想要退出，取消FFmpeg任务
                self.ffmpeg.cancel()
                break

        # 等待FFmpeg任务完成
        await asyncio.wait([ff_task])
        desc_task.cancel()  # 取消描述循环任务

        return ff_task.result()

    def run(self) -> bool:
        """
        运行应用的主方法

        这是应用的主要入口点，执行以下流程：
        1. 参数验证
        2. 输入输出文件检查
        3. 文件存在性验证
        4. 执行FFmpeg命令
        5. 结果处理和错误处理

        Returns:
            bool: 执行是否成功

        Raises:
            SafeError: 当发生可恢复的错误时
        """
        # 验证参数
        if not self.arguments:
            raise SafeError("未提供任何参数。")

        if not appenv.ffmpeg_executable:
            raise SafeError("当前环境中未找到 [cx.filepath]ffmpeg[/] 可执行文件。")

        # 开始检查输入输出
        appenv.whisper("检查输入输出……")
        inputs = list(self.input_files())
        outputs = list(self.output_files())

        # 显示输入输出文件列表
        appenv.whisper(
            IndexedListPanel(inputs, title="输入文件"),
            IndexedListPanel(outputs, title="输出文件"),
        )

        # 验证输入文件
        if not inputs:
            raise SafeError("没有提供需要处理的文件，请使用 -i 参数指定输入文件。")

        if not outputs:
            raise SafeError("没有提供输出文件，请指定输出选项及目标文件。")

        # 检查输入文件是否存在
        for i in inputs:
            if not Path(i).exists():
                raise SafeError(f"输入文件 {i} 不存在。")

        # 检查输出文件是否已存在
        existed_outputs = [x for x in outputs if Path(x).exists()]
        if existed_outputs and "-y" not in self.arguments:
            appenv.whisper(IndexedListPanel(existed_outputs, title="已存在的输出文件"))
            raise SafeError("请使用 -y 参数覆盖已存在的文件。")

        # 创建不存在的输出目录
        non_exist_dirs = filter(
            lambda x: not x.exists(), [Path(a).parent for a in outputs]
        )
        if non_exist_dirs:
            for d in non_exist_dirs:
                d.mkdir(parents=True, exist_ok=True)
            appenv.whisper(IndexedListPanel(non_exist_dirs, title="创建的输出目录"))

        # 执行FFmpeg命令
        result = asyncio.run(self.execute(self.arguments))

        appenv.whisper("运行结果：{}".format(result))

        # 处理执行结果
        if not result:
            if self.ffmpeg.is_canceled:
                raise SafeError("[cx.warning]用户取消了操作。[/]")
            else:
                raise SafeError("[cx.error]操作失败，请排查问题。[/]")

        return result
