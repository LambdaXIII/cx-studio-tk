import asyncio
import json
from pathlib import Path
from typing import Any

from cx_studio.filesystem.path_expander import CmdFinder
from cx_studio.iotools import AsyncStreamUtils
from cx_tools.app.safe_error import SafeError
from .appenv import appenv
from .info_elements import MediaInfo


class Prober:
    def __init__(self, ffprobe_executable: str | Path | None = None):
        # 尝试找到ffprobe可执行文件，如果没有指定，则使用默认路径
        self._ffprobe_executable = str(CmdFinder.which(ffprobe_executable or "ffprobe"))

    async def get_details(self, file: Path) -> dict[str, Any]:
        """使用ffprobe获取媒体文件的详细信息"""
        args = [
            self._ffprobe_executable,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file),
        ]

        process = await AsyncStreamUtils.create_subprocess(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="ignore").strip()
            raise SafeError(f"ffprobe执行失败: {error_msg}")

        try:
            return json.loads(stdout.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise SafeError(f"解析ffprobe输出失败: {str(e)}")

    def probe(self, file: Path) -> dict[str, Any]:
        """同步获取媒体文件的详细信息"""
        details = asyncio.run(self.get_details(file))
        media_info = MediaInfo(details)
        appenv.say(media_info)
