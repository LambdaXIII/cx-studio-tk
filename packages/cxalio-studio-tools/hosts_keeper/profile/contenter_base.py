from abc import ABC, abstractmethod
from box import Box
from .hostrecord import HostRecord
from typing import AsyncGenerator

from pathlib import Path


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
        **kwargs,
    ) -> None:
        super().__init__()
        self.package = package if isinstance(package, Box) else Box(package)
        self.package.update(kwargs)
        self.profile_metadata = (
            profile_metadata
            if isinstance(profile_metadata, Box)
            else Box(profile_metadata)
        )

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
    def register_contenter(cls: type[AbstractContenter]) -> None:
        """注册内容器"""
        ContenterBase.CONTENTERS[cls.SCHEMA] = cls

    @staticmethod
    def create_contenter(
        schema: str,
        package: Box | dict | None = None,
        profile_metadata: Box | dict | None = None,
        **kwargs,
    ) -> type[AbstractContenter] | None:
        """获取内容器"""
        return (
            ContenterBase.CONTENTERS.get(schema)(package, profile_metadata, **kwargs)
            if schema in ContenterBase.CONTENTERS
            else None
        )
