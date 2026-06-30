"""Jpegger 应用入口。

`JpeggerApp` 实现 `IApplication` 接口，管理应用生命周期：
`start()` 解析参数 → `run()` 构建过滤器链与任务并执行 → `stop()` 清理。
"""

import sys
from collections.abc import Sequence
from typing import override

from cx_tools.app import IApplication
from cx_tools.i18n import _
from cx_wealth import IndexedListPanel, WealthDetailPanel, WealthLabel

from .appenv import appenv
from .components.mission_runner import MissionRunner
from .simple_appcontext import SimpleAppContext, SimpleHelp
from .simple_filter_chain_builder import SimpleFilterChainBuilder
from .simple_mission_builder import SimpleMissionBuilder


class JpeggerApp(IApplication):
    """Jpegger 主应用。

    Args:
        arguments: 命令行参数序列；None 时使用 `sys.argv[1:]`。
    """

    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments or sys.argv[1:])

    @override
    def start(self) -> None:
        """解析命令行参数并初始化应用环境。"""
        appenv.context = SimpleAppContext.from_arguments(self.sys_arguments)
        appenv.start()

    @override
    def stop(self) -> None:
        """停止应用环境。"""
        appenv.stop()

    @override
    def run(self) -> None:
        """执行业务逻辑：帮助、构建链、构建任务、运行任务。"""
        if appenv.context is None:
            raise RuntimeError(_("应用上下文尚未初始化"))

        # 帮助分支。
        if appenv.context.show_help:
            SimpleHelp.show_help(appenv.console)
            return

        if appenv.context.show_full_help:
            SimpleHelp.show_full_help(appenv.console)
            return

        # 在调试模式下展示解析后的参数。
        appenv.whisper(WealthDetailPanel(appenv.context, title="初始化参数"))

        filter_chain = SimpleFilterChainBuilder.build_filter_chain_from_simple_context(
            appenv.context
        )
        appenv.whisper(WealthDetailPanel(filter_chain, title="过滤器链"))

        # 空输入时短路返回。
        if not appenv.context.inputs:
            appenv.say(_("未指定输入文件，无事可做"))
            return

        builder = SimpleMissionBuilder(filter_chain, appenv.context)
        missions = builder.make_missions(appenv.context.inputs)

        appenv.whisper(
            IndexedListPanel([WealthLabel(x) for x in missions], title="任务列表")
        )

        runner = MissionRunner(missions)
        runner.run()
