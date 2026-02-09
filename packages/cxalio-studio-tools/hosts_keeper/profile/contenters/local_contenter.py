import asyncio
from typing import override, AsyncGenerator
from ..hostrecord import HostRecord
from ..contenter_base import AbstractContenter, ContenterBase
from box import Box
from pathlib import Path


class LocalContenter(AbstractContenter):
    """本地内容器"""

    SCHEMA: str = "local_content"

    def __init__(
        self,
        package: Box | dict | None = None,
        profile_metadata: Box | dict | None = None,
        **kwargs
    ) -> None:
        super().__init__(package, profile_metadata, **kwargs)
        self.file: str = self.package.get("file")
        self.description: str | None = self.package.get("description")
        self.encoding: str = self.package.get("encoding") or "utf-8"

    @property
    def file_path(self) -> Path | None:
        """文件路径"""
        if self.file is None:
            return None

        path = Path(self.file)
        if path.is_absolute():
            return path

        profile_path = self.profile_path
        if profile_path is None:
            return path.resolve()

        return (profile_path / path).resolve()

    @override
    async def iter_records(self) -> AsyncGenerator[HostRecord, None]:
        """迭代记录"""
        file_path = self.file_path
        if file_path is None or not file_path.exists():
            return
        with open(file_path, "r", encoding=self.encoding) as f:
            for line in f.readlines():
                await asyncio.sleep(0)
                record = HostRecord.from_line(line.strip())
                yield record


ContenterBase.register_contenter(LocalContenter)
