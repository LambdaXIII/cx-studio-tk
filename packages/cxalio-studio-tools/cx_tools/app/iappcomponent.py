"""IAppComponent — CLI 特化组件抽象基类。

CLI 工具中需要同时持有 appenv 和 context 的非 IApplication 组件继承此类。
不继承此类的组件属于通用功能组件，不得依赖 appenv 或 context。
"""

from abc import ABC

from cx_tools.app.iappcontext import IAppContext
from cx_tools.app.iappenv import IAppEnvironment


class IAppComponent(ABC):
    """CLI 特化组件基类。

    __init__ 提供 (appenv, context) 签名契约，子类按需自行存储和消费。
    IApplication 子类必须接收这两个参数；
    其他 IAppComponent 子类按实际需求决定存储哪些、如何暴露。
    """

    def __init__(
        self,
        appenv: IAppEnvironment | None = None,
        context: IAppContext | None = None,
    ) -> None:
        """初始化组件。__init__ 签名仅作契约提示，不在此存储参数。"""
        pass
