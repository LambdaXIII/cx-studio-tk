import os, shutil
from collections.abc import Generator, Sequence, Collection, Iterable, Mapping
from pathlib import Path, PurePath


from cx_studio.path_expander.cx_executablevalidator import ExecutableValidator
from cx_studio.path_expander.cx_pathexpander import PathExpander
from cx_studio.utils import PathUtils
import itertools


class CmdFinder:
    def __init__(
        self,
        search_dirs: Collection | Iterable | None = None,
        inlude_cwd: bool = False,
        include_env_paths: bool = True,
        expand_extensions: bool = True,
        recursive: bool = False,
        use_clue: bool = True,
    ):
        self._search_dirs = search_dirs or []
        self._inlude_cwd = inlude_cwd
        self._include_env_paths = include_env_paths
        self._expand_extensions = expand_extensions
        self._recursive = recursive
        self._use_clue = use_clue

    def iter_included_dirs(self) -> Generator[Path, None, None]:
        if self._inlude_cwd:
            yield Path.cwd()
        if self._include_env_paths:
            os_path = os.environ.get("PATH")
            for path in (os_path if os_path else "").split(os.pathsep):
                yield Path(path)
        for path in self._search_dirs:
            yield Path(path)

    @staticmethod
    def __is_result_ok(result: PurePath | str) -> bool:
        x = Path(result)
        return x.is_absolute() and x.exists() and os.access(x, os.X_OK)

    def find(self, cmd: str | Path) -> Path | None:
        cmd = str(cmd)
        path = Path(cmd).resolve()
        if self.__is_result_ok(path):
            return path.resolve()

        path = Path(str(shutil.which(cmd)))
        if self.__is_result_ok(path):
            return path.resolve()

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
            search_dirs = expander.expand(*search_dirs)

        cmd_names = [cmd]
        if self._expand_extensions:
            if not cmd.lower().endswith(".com"):
                cmd_names.append(cmd.strip(".") + ".com")
            if not cmd.lower().endswith(".exe"):
                cmd_names.append(cmd.strip(".") + ".exe")
            p = Path(cmd)
            if p.suffix == ".exe":
                cmd_names.append(str(p.with_suffix(".com")))
            if p.suffix == ".com":
                cmd_names.append(str(p.with_suffix(".exe")))

        for dir, name in itertools.product(search_dirs, cmd_names):
            if not dir.is_dir():
                continue
            path = dir / name
            if self.__is_result_ok(path):
                return path.resolve()

        return None

    @classmethod
    def which(cls, cmd: str | Path) -> Path | None:
        finder = cls()
        return finder.find(cmd)
