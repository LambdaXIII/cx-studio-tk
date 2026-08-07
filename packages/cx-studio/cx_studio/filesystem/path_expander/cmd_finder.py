"""CmdFinder — 可执行文件查找器。

提供跨平台的可执行文件搜索能力，支持：
- 直接调用 ``shutil.which()`` 快速定位 PATH 上的命令
- 遍历 ``PATH`` 环境变量中的目录进行手动搜索
- 对 Windows ``.exe`` / ``.com`` 扩展名自动补全
- 灵活的搜索目录配置（环境 PATH、CWD、自定义目录、递归展开）

典型用法：:

    from cx_studio.filesystem import CmdFinder

    path = CmdFinder.which("ffmpeg")
    if path is None:
        print("ffmpeg 未找到")
    else:
        print(f"ffmpeg 位于 {path}")
"""

import itertools
import os
import shutil
from collections.abc import Generator, Collection, Iterable
from pathlib import Path, PurePath

from .path_expander import PathExpander


class CmdFinder:
    """可执行文件查找器。

    通过多阶段策略查找可执行文件：

    1. 若 ``cmd`` 本身已存在且可执行，直接返回解析后的绝对路径
    2. 调用 ``shutil.which()`` 按系统规范查找
    3. 遍历配置的搜索目录，依次尝试原始名 + 扩展名变体

    Parameters:
        search_dirs: 额外搜索目录列表
        include_cwd: 是否将当前工作目录加入搜索目录
        include_env_paths: 是否读取 ``PATH`` 环境变量加入搜索目录
        expand_extensions: 是否在 Windows 上自动补全 ``.exe`` / ``.com`` 扩展名
        recursive: 是否递归展开搜索目录（使用 ``PathExpander``）
        use_clue: 当 ``cmd`` 包含路径分隔符时，是否将其父目录加入搜索目录
    """

    def __init__(
        self,
        search_dirs: Collection | Iterable | None = None,
        include_cwd: bool = False,
        include_env_paths: bool = True,
        expand_extensions: bool = True,
        recursive: bool = False,
        use_clue: bool = True,
    ):
        self._search_dirs = search_dirs or []
        self._include_cwd = include_cwd
        self._include_env_paths = include_env_paths
        self._expand_extensions = expand_extensions
        self._recursive = recursive
        self._use_clue = use_clue

    def iter_included_dirs(self) -> Generator[Path, None, None]:
        """生成所有搜索目录。

        Yield 顺序：CWD（若启用）→ ``PATH`` 条目 → 自定义目录。
        """
        if self._include_cwd:
            yield Path.cwd()
        if self._include_env_paths:
            os_path = os.environ.get("PATH")
            for entry in (os_path if os_path else "").split(os.pathsep):
                yield Path(entry)
        for path in self._search_dirs:
            yield Path(path)

    @staticmethod
    def _is_result_ok(result: PurePath | str) -> bool:
        """判断给定路径是否指向一个存在的可执行文件。

        ``Path`` 内部操作确保任何存在的路径都可以表达为绝对路径，
        因此不要求 ``result`` 本身是绝对路径——``find()`` 的返回值
        统一通过 ``resolve()`` 转为绝对路径。

        Returns:
            True 当且仅当路径存在且可执行。
        """
        x = Path(result)
        return x.exists() and os.access(x, os.X_OK)

    def find(self, cmd: str | Path) -> Path | None:
        """查找可执行文件路径。

        搜索策略（依次进行，命中即返回）：
        1. 对 ``cmd`` 做 ``resolve()``，检查是否已存在且可执行
        2. 调用 ``shutil.which(cmd)`` 按系统规范搜索
        3. 遍历所有搜索目录，依次尝试原始命令名及扩展名变体

        Args:
            cmd: 要查找的命令名或路径（如 ``"ffmpeg"``、``"/usr/bin/ffmpeg"``）

        Returns:
            解析后的绝对路径，未找到时返回 ``None``
        """
        cmd = str(cmd)

        # 策略 1：cmd 本身已存在且可执行
        path = Path(cmd).resolve()
        if self._is_result_ok(path):
            return path.resolve()

        # 策略 2：shutil.which() 按系统规范查找
        which_result = shutil.which(cmd)
        if which_result is not None and self._is_result_ok(Path(which_result)):
            return Path(which_result).resolve()

        # 策略 3：遍历搜索目录
        search_dirs = list(self.iter_included_dirs())

        if self._use_clue:
            p = Path(cmd)
            if len(p.parts) > 1:
                clue_dir = p.parent.resolve()
                search_dirs.append(clue_dir)

        if self._recursive:
            expander = PathExpander(
                PathExpander.StartInfo(
                    accept_files=False,
                )
            )
            search_dirs = list(expander.expand(*search_dirs))

        cmd_names = [cmd]
        if self._expand_extensions:
            if not cmd.lower().endswith(".com"):
                cmd_names.append(cmd.strip(".") + ".com")
            if not cmd.lower().endswith(".exe"):
                cmd_names.append(cmd.strip(".") + ".exe")
            # Windows 上 .exe 和 .com 互相替换
            p = Path(cmd)
            if p.suffix == ".exe":
                cmd_names.append(str(p.with_suffix(".com")))
            if p.suffix == ".com":
                cmd_names.append(str(p.with_suffix(".exe")))
            # 注：上述展开会产生少量噪音条目（如 "ffmpeg.exe.com"），
            # 这是有意为之的冗余设计——实际文件系统中几乎不会出现
            # 此类双重扩展名，不会导致误判。

        # TODO: 未来可扩展对脚本文件（.cmd / .bat / .ps1）的支持。
        # 当前仅搜索原生可执行文件（.exe / .com），脚本文件的查找
        # 依赖 shutil.which() 的 PATHEXT 处理。若需在 fallback 搜索中
        # 也覆盖脚本扩展名，在此处追加对应的扩展名变体。

        for dir_entry, name in itertools.product(search_dirs, cmd_names):
            if not dir_entry.is_dir():
                continue
            trial = dir_entry / name
            if self._is_result_ok(trial):
                return trial.resolve()

        return None

    @classmethod
    def which(cls, cmd: str | Path) -> Path | None:
        """快速查找可执行文件。

        使用默认配置（只搜索 ``PATH``，启用扩展名展开，不递归）的快捷方法。

        Args:
            cmd: 要查找的命令名或路径

        Returns:
            解析后的绝对路径，未找到时返回 ``None``
        """
        finder = cls()
        return finder.find(cmd)
