from ..hostrecord import HostRecord
from ..contenter_base import AbstractContenter, ContenterBase
from box import Box
from typing import override, AsyncGenerator


class DirectContenter(AbstractContenter):
    """直接内容器"""

    SCHEMA: str = "direct_content"

    def __init__(
        self,
        package: Box | dict | None = None,
        profile_metadata: Box | dict | None = None,
        **kwargs
    ) -> None:
        super().__init__(package, profile_metadata, **kwargs)
        self.ip: str | None = self.package.get("ip") or None
        self.domains: list[str] = self.package.get("domains") or []
        self.comment: str | None = self.package.get("comment") or None

    @override
    async def iter_records(self) -> AsyncGenerator[HostRecord, None]:
        yield HostRecord(self.ip, self.domains, self.comment)


ContenterBase.register_contenter(DirectContenter)
