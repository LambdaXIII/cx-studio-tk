"""FFPretty 命令行上下文。

持有 argparse 解析后的参数：debug/pretend/overwrite/no-overwrite
以及剩余的 FFmpeg 原始参数。
"""

from argparse import ArgumentParser
from collections.abc import Sequence

from cx_tools.app import IAppContext, SafeError
from ffpretty.i18n import _


class FFPrettyContext(IAppContext):
    """FFPretty 命令行上下文。

    职责：
    - 持有命令行参数解析结果
    - 提供 ffmpeg 可执行文件路径（惰性查找）
    - 实现 IAppContext 上下文管理器协议
    """

    def __init__(self) -> None:
        super().__init__()
        self.debug_mode: bool = False
        self.pretending_mode: bool = False
        self.overwrite: bool = False
        self.no_overwrite: bool = False
        self.arguments: list[str] = []
        self.ffmpeg_executable: str | None = None

    @classmethod
    def from_arguments(cls, arguments: Sequence[str]) -> "FFPrettyContext":
        """从命令行参数构造上下文。

        Args:
            arguments: 命令行参数列表（不含程序名）。

        Returns:
            构造好的 FFPrettyContext 实例。

        Raises:
            SafeError: 当 -y 和 -n 同时使用时。
        """
        ctx = cls()
        parser = ArgumentParser(add_help=False)
        parser.add_argument("-d", "--debug", action="store_true")
        parser.add_argument("--pretend", action="store_true")
        parser.add_argument("-y", "--overwrite", action="store_true")
        parser.add_argument("-n", "--no-overwrite", action="store_true")
        parsed, unknowns = parser.parse_known_args(list(arguments))

        ctx.debug_mode = parsed.debug
        ctx.pretending_mode = parsed.pretend
        ctx.overwrite = parsed.overwrite
        ctx.no_overwrite = parsed.no_overwrite
        ctx.arguments = list(unknowns)

        if parsed.overwrite and parsed.no_overwrite:
            raise SafeError(_("-y/--overwrite 与 -n/--no-overwrite 不可同时使用。"))

        from cx_studio.filesystem.path_expander import CmdFinder

        result = CmdFinder.which("ffmpeg")
        ctx.ffmpeg_executable = str(result) if result else None

        return ctx
