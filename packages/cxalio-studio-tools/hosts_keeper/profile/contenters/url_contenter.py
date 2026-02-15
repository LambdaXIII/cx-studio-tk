import asyncio
from typing import override, AsyncGenerator
import urllib.request
from ..hostrecord import HostRecord
from ..contenter_base import AbstractContenter, ContenterBase
from box import Box


class UrlContenter(AbstractContenter):
    """URL内容器"""

    SCHEMA: str = "url_content"

    def __init__(
        self,
        package: Box | dict | None = None,
        profile_metadata: Box | dict | None = None,
        **kwargs
    ) -> None:
        super().__init__(package, profile_metadata, **kwargs)
        self.url: str | None = self.package.get("url")
        self.description: str | None = self.package.get("description")
        self.encoding: str = self.package.get("encoding") or "utf-8"

    def get_content(self) -> str:
        """获取URL内容"""
        # TODO:改进为异步获取
        if self.url is None:
            return ""
        with urllib.request.urlopen(self.url) as response:
            return response.read().decode(self.encoding)

    @override
    async def iter_records(self) -> AsyncGenerator[HostRecord, None]:
        """迭代记录"""
        content = self.get_content()
        for line in content.splitlines():
            await asyncio.sleep(0)
            yield HostRecord.from_line(line.strip())


ContenterBase.register_contenter(UrlContenter)
