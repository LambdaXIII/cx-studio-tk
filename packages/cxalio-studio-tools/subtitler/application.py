"""Subtitler 应用入口。

`SubtitlerApplication` 实现 `IApplication` 接口，管理应用生命周期：
`start()` 注入 debug 模式 → `run()` 路由帮助或执行转换 → `__exit__` 捕获
SafeError / KeyboardInterrupt 输出友好提示（错误走 stderr）。横幅展示由
`SubtitlerEnv.start()` 负责，本应用只做装配。
"""

from typing import override

from cx_tools.app import IAppEnvironment, IApplication, SafeError

from .app_help import SubtitlerHelp
from .appcontext import SubtitlerContext
from .components import SubtitlerConverter
from .i18n import _


class SubtitlerApplication(IApplication):
    """Subtitler 主应用。

    Args:
        appenv: 应用环境实例。
        context: 命令行上下文。
    """

    def __init__(
        self,
        appenv: IAppEnvironment,
        context: SubtitlerContext,
    ):
        super().__init__(appenv, context)
        self.context = context

    @override
    def start(self) -> None:
        """启动应用：注入 debug 模式。"""
        self.appenv.set_debug_mode(self.context.debug_mode)

    @override
    def stop(self) -> None:
        """停止应用。无工具特定清理。"""
        pass

    @override
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """退出应用。始终执行 stop()，捕获已知异常类型输出友好提示。"""
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is not None and issubclass(exc_type, SafeError):
            self.appenv.say(f"[{exc_val.style}]{exc_val}[/]")
            result = True
        elif exc_type is KeyboardInterrupt:
            self.appenv.say(f"[cx.warning]{_('用户中断')}[/]")
            result = True
        return result

    @override
    def run(self) -> None:
        """执行应用主逻辑：帮助路由，否则执行一次格式转换。"""
        ctx = self.context
        if ctx.show_help:
            SubtitlerHelp(self.appenv, ctx).show_help()
            return
        if ctx.show_full_help:
            SubtitlerHelp(self.appenv, ctx).show_full_help()
            return
        SubtitlerConverter(self.appenv, ctx).convert()
