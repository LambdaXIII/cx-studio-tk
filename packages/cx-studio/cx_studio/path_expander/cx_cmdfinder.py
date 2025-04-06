import os
from collections.abc import Generator
from pathlib import Path

from cx_studio.path_expander.cx_executablevalidator import ExecutableValidator
from cx_studio.path_expander.cx_pathexpander import PathExpander
from cx_studio.utils import PathUtils


class CmdFinder:

    @staticmethod
    def default_folders():
        os_path = os.environ.get("PATH")
        paths = (os_path if os_path else "").split(os.pathsep)
        yield from paths
        yield Path.home()
        yield Path.home() / ".bin"
        yield Path.home() / ".local/bin"

    def __init__(
        self, *folders, include_cwd: bool = True, include_default_folders: bool = True
    ):
        self._folders: list[str | Path] = [Path(x) for x in folders]
        self._include_cwd = include_cwd
        self._include_default_folders = include_default_folders

    def add_folder(self, folder: str | Path) -> "CmdFinder":
        self._folders.append(folder)
        return self

    def remove_folder(self, folder: str | Path) -> "CmdFinder":
        self._folders.remove(folder)
        return self

    def folders(self) -> Generator[str | Path, None, None]:
        if self._include_cwd:
            yield Path.cwd()

        if self._include_default_folders:
            yield from CmdFinder.default_folders()

        yield from self._folders

    def find(self, cmd: str) -> str | None:
        cmd = str(cmd)
        targets = {cmd}
        if os.name == "nt":
            targets.add(str(PathUtils.force_suffix(cmd, "exe")))
            targets.add(str(PathUtils.force_suffix(cmd, "com")))

        expander_info = PathExpander.StartInfo(
            accept_dirs=False,
            accept_others=False,
            follow_symlinks=True,
            file_validator=ExecutableValidator(),
        )

        expander = PathExpander(expander_info)
        for folder in self.folders():
            dir = PathUtils.take_dir(PathUtils.normalize_path(folder))
            for x in expander.expand(dir):
                d = Path(x)
                for name in targets:
                    if d.name == name:
                        return str(d)

        return None
