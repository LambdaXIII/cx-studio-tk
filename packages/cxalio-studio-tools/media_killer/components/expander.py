"""源文件展开器。

处理命令行输入的源路径展开为最终媒体文件列表。
三阶段展开：项目文件解析（委托 media_scout.InspectorChain）→ 目录递归 → 后缀过滤。
后缀过滤集合由 Application 合并所有 Preset 的 source_suffixes 后传入。
"""

from collections.abc import Generator
from pathlib import Path

from media_scout.common.inspectors import InspectorChain
from media_scout.common.inspectors.inspector_info import InspectorInfo

# 项目文件扩展名集合
_PROJECT_FILE_EXTENSIONS: set[str] = {
    ".edl",  # EDL 剪辑决定表
    ".xml",  # FCP 7 XML
    ".fcpxml",  # FCPX XML
    ".fcpxmld",  # FCPX XML (目录)
    ".csv",  # DaVinci Resolve CSV
    ".txt",  # 纯文本路径列表
}


class SourceExpander:
    """源文件展开器。

    处理顺序：
    1. 项目文件解析（调用 media_scout.InspectorChain）
    2. 目录递归
    3. 后缀过滤

    路径解析规则：
    - 命令行输入的相对路径基于 CWD 解析为绝对路径
    - 项目文件内部路径基于项目文件位置解析
    """

    def __init__(
        self,
        suffixes: set[str],
        scout_chain: InspectorChain | None = None,
    ) -> None:
        """初始化源文件展开器。

        Args:
            suffixes: 允许的源文件后缀集合
            scout_chain: 项目文件解析器。若为 None，则不解析项目文件。
        """
        self._suffixes = {s.lower() for s in suffixes}
        self._scout_chain = scout_chain

    def expand(self, *paths: str | Path) -> Generator[Path, None, None]:
        """展开路径列表，返回所有符合条件的源文件。

        Args:
            paths: 路径列表（可以是文件、目录、项目文件）

        Yields:
            Path: 符合条件的源文件路径（绝对路径）
        """
        for path in paths:
            path = Path(path).resolve()  # 基于 CWD 解析为绝对路径

            if not path.exists():
                continue

            if path.is_file():
                if self._is_project_file(path):
                    # 项目文件：调用 scout_chain 解析
                    yield from self._expand_project_file(path)
                elif path.suffix.lower() in self._suffixes:
                    # 普通文件：检查后缀
                    yield path
            elif path.is_dir():
                # 目录：递归展开
                yield from self._expand_directory(path)

    def _expand_directory(self, directory: Path) -> Generator[Path, None, None]:
        """递归展开目录中的符合条件的的文件。

        Args:
            directory: 目录路径

        Yields:
            Path: 符合条件的源文件路径
        """
        for item in directory.rglob("*"):
            if item.is_file() and item.suffix.lower() in self._suffixes:
                yield item

    def _expand_project_file(self, project_file: Path) -> Generator[Path, None, None]:
        """展开项目文件，解析其中引用的媒体路径。

        Args:
            project_file: 项目文件路径

        Yields:
            Path: 符合条件的源文件路径
        """
        if self._scout_chain is None:
            return

        # 调用 scout_chain 解析项目文件
        info = InspectorInfo(project_file)
        for media_path in self._scout_chain.inspect(info):
            media_path = Path(media_path)
            # media_path 可能是相对路径，需要基于项目文件目录解析
            if not media_path.is_absolute():
                media_path = (project_file.parent / media_path).resolve()

            if media_path.exists() and media_path.suffix.lower() in self._suffixes:
                yield media_path

    def _is_project_file(self, path: Path) -> bool:
        """判断文件是否为项目文件。

        基于扩展名判断，不探测文件内容。

        Args:
            path: 文件路径

        Returns:
            bool: 是否为项目文件
        """
        return path.suffix.lower() in _PROJECT_FILE_EXTENSIONS
