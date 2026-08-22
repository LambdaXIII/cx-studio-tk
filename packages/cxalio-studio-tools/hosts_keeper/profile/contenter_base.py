from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator

from box import Box

from .hostrecord import HostRecord


class AbstractContenter(ABC):
    """
    内容器基类。
    根据SHEMA确定需要处理的段落。
    """

    SCHEMA: str = ""

    def __init_subclass__(cls) -> None:
        if cls.SCHEMA == "":
            raise TypeError(f"子类 {cls.__name__} 必须重定义SCHEMA常量")

    def __init__(
        self,
        package: Box | dict | None = None,
        profile_metadata: Box | dict | None = None,
        appenv=None,
        **kwargs,
    ) -> None:
        super().__init__()
        self._appenv = appenv
        pkg = package if isinstance(package, Box) else Box(package)
        pkg.update(kwargs)
        self.package = pkg
        self.profile_metadata = (
            profile_metadata
            if isinstance(profile_metadata, Box)
            else Box(profile_metadata)
        )

        # 动态状态文本：contenter 在 iter_records 过程中自行更新，
        # 外部通过 on_contenter_status 回调读取以更新 progress。
        # 初始值由子类在 __init__ 中设置（通常为描述性文本）。
        self.status_text: str = ""

    @property
    def profile_path(self) -> Path | None:
        """配置文件路径"""
        if self.profile_metadata is None:
            return None
        p = self.profile_metadata.get("path")
        if p is None:
            return None
        return Path(p)

    @abstractmethod
    async def iter_records(self) -> AsyncGenerator[HostRecord, None]:
        pass


class ContenterBase:
    """内容器管理器"""

    CONTENTERS: dict[str, type[AbstractContenter]] = {}

    @staticmethod
    def register_contenter(contenter_cls: type[AbstractContenter]) -> None:
        """注册内容器"""
        ContenterBase.CONTENTERS[contenter_cls.SCHEMA] = contenter_cls

    @staticmethod
    def create_contenter(
        schema: str,
        package: Box | dict | None = None,
        profile_metadata: Box | dict | None = None,
        appenv=None,
        **kwargs,
    ) -> AbstractContenter | None:
        """获取内容器"""
        cls = ContenterBase.CONTENTERS.get(schema)
        if cls is None:
            return None
        return cls(package, profile_metadata, appenv=appenv, **kwargs)
