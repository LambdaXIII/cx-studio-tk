"""IApplication — 应用抽象基类。"""

import sys
from abc import abstractmethod
from typing import Self

from cx_tools.app.iappcontext import IAppContext
from cx_tools.app.iappenv import IAppEnvironment
from cx_tools.app.iappcomponent import IAppComponent


class IApplication(IAppComponent):
    """应用抽象基类。

    职责：编排 appenv + context，驱动应用生命周期。
    不绑定特定 appenv 单例，可被挂载到任何兼容的 IAppEnvironment。

    生命周期：
        with IApplication(appenv, context) as app:
            app.run()
    ── 进入时启动 context，退出时停止 context。appenv 的上下文
      在 Application 外部管理（`with appenv:` 嵌套 `with Application(...)`）。

    子类覆盖约定：
    - __init__ 调用 super().__init__(appenv, context) 后自行赋值
      self.appenv = appenv 和 self.context = context（后者用具体子类类型收窄类型）
    - start() 做工具特定的启动工作（如连接数据库、注册中断回调），
      不负责启动 appenv——appenv 已在外部上下文中启动
    - stop() 做工具特定的清理工作，不负责停止 appenv——
      appenv 在外部上下文退出时停止
    - __exit__ 覆盖时必须调用 super().__exit__()——它负责调用 self.stop() 和
      self.context.__exit__()（context 的资源清理）。如果子类在 __exit__ 中
      返回 True 抑制异常传播，仍需确保 super().__exit__() 被调用以执行 context 清理。
      正确模式：
          def __exit__(self, exc_type, exc_val, exc_tb):
              result = super().__exit__(exc_type, exc_val, exc_tb)  # stop + context 清理
              if exc_type is KeyboardInterrupt:
                  self.appenv.say("用户中断")
                  result = True
              return result
    """

    def __init__(
        self,
        appenv: IAppEnvironment,
        context: IAppContext,
    ) -> None:
        super().__init__(appenv, context)
        self.appenv = appenv
        self.context = context

    @abstractmethod
    def start(self) -> None:
        """启动应用。子类在此做工具特定的启动工作（如连接数据库、注册中断回调）。"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """停止应用。子类在此做工具特定的清理工作。"""
        pass

    def __enter__(self) -> Self:
        self.context.__enter__()
        try:
            self.start()
        except:
            self.context.__exit__(*sys.exc_info())
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        try:
            self.stop()
        finally:
            self.context.__exit__(exc_type, exc_val, exc_tb)
        return False

    @abstractmethod
    def run(self) -> None:
        """执行应用主逻辑。"""
        pass
