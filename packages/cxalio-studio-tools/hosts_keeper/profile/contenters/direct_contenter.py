from typing import override, AsyncGenerator
from hosts_keeper.i18n import _


from box import Box

from ..contenter_base import AbstractContenter, ContenterBase
from ..hostrecord import HostRecord


class DirectContenter(AbstractContenter):
    """直接内容器"""

    SCHEMA: str = "direct_content"

    def __init__(
        self,
        package: Box | dict | None = None,
        profile_metadata: Box | dict | None = None,
        appenv=None,
        **kwargs,
    ) -> None:
        super().__init__(package, profile_metadata, appenv=appenv, **kwargs)
        self.ip: str | None = self.package.get("ip") or None
        self.domains: list[str] = self.package.get("domains") or []
        self.comment: str | None = self.package.get("comment") or None

        self.status_text = _("直接内容")

    @override
    async def iter_records(self) -> AsyncGenerator[HostRecord, None]:  # type: ignore[override]  # pyright async generator 覆盖类型推断限制
        yield HostRecord(self.ip, self.domains, self.comment)


ContenterBase.register_contenter(DirectContenter)
