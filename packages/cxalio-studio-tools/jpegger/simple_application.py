"""Jpegger 应用入口。

`JpeggerApp` 实现 `IApplication` 接口，管理应用生命周期：
`start()` 解析参数 → `run()` 构建过滤器链与任务并执行 → `stop()` 清理。
"""

from typing import override

from cx_tools.app import IApplication, IAppEnvironment
from cx_wealthy import IndexedListPanel, RichLabel, WealthyDetailPanel
from jpegger.i18n import _

from .components.mission_runner import MissionRunner
from .simple_appcontext import SimpleAppContext, JpeggerHelp
from .simple_filter_chain_builder import SimpleFilterChainBuilder
from .simple_mission_builder import SimpleMissionBuilder


class JpeggerApp(IApplication):
    """Jpegger 主应用。

    Args:
        appenv: 应用环境实例。
        context: 命令行上下文。
    """

    def __init__(
        self,
        appenv: IAppEnvironment,
        context: SimpleAppContext,
    ):
        super().__init__(appenv, context)
        self.context = context

    @override
    def start(self) -> None:
        """解析命令行参数并初始化应用环境。"""
        self.appenv.set_debug_mode(self.context.debug_mode)

    @override
    def stop(self) -> None:
        """停止应用环境。"""
        pass

    @override
    def run(self) -> None:
        """执行业务逻辑：帮助、构建链、构建任务、运行任务。"""
        # 帮助分支。
        if self.context.show_help:
            help_component = JpeggerHelp(self.appenv, self.context)
            help_component.show_help()
            return

        if self.context.show_full_help:
            help_component = JpeggerHelp(self.appenv, self.context)
            help_component.show_full_help()
            return

        # 在调试模式下展示解析后的参数。
        self.appenv.whisper(WealthyDetailPanel(self.context, title="初始化参数"))

        filter_chain = SimpleFilterChainBuilder.build_filter_chain_from_simple_context(
            self.context
        )
        self.appenv.whisper(WealthyDetailPanel(filter_chain, title="过滤器链"))

        # 空输入时短路返回。
        if not self.context.inputs:
            self.appenv.say(_("未指定输入文件，无事可做"))
            return

        builder = SimpleMissionBuilder(filter_chain, self.context)
        missions = builder.make_missions(self.context.inputs)

        self.appenv.whisper(
            IndexedListPanel([RichLabel(x) for x in missions], title="任务列表")
        )

        runner = MissionRunner(
            appenv=self.appenv, context=self.context, missions=missions
        )
        runner.run()
