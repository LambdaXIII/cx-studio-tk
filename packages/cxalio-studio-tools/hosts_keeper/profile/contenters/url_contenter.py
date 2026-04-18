import asyncio
import urllib.error
import urllib.request
from typing import override, AsyncGenerator

from box import Box

from ..contenter_base import AbstractContenter, ContenterBase
from ..hostrecord import HostRecord
from ...appenv import appenv


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
        if self.url is None:
            return ""

        content_bytes: bytes = b""
        try:
            with urllib.request.urlopen(self.url, timeout=10) as response:
                content_bytes = response.read()

                content_type = response.headers.get_content_charset()
                if content_type:
                    return content_bytes.decode(content_type)

                return content_bytes.decode(self.encoding)

        except urllib.error.URLError as e:
            appenv.say(f"[cx.error]无法获取 URL 内容: {e}")
            return ""
        except UnicodeDecodeError:
            appenv.whisper(f"[cx.info]使用配置编码 {self.encoding} 解码失败，尝试 utf-8 回退...")
            try:
                return content_bytes.decode("utf-8", errors="replace")
            except Exception:
                return ""

    @override
    async def iter_records(self) -> AsyncGenerator[HostRecord, None]:
        """迭代记录"""
        content = self.get_content()
        for line in content.splitlines():
            await asyncio.sleep(0)
            yield HostRecord.from_line(line.strip())


ContenterBase.register_contenter(UrlContenter)
