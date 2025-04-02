from dataclasses import dataclass
from pathlib import Path

from .cx_pathvalidator import IPathValidator, ChainValidator


@dataclass
class PathExpanderStartInfo:
    anchor_point: Path | None = None
    expand_subdir: bool = True
    accept_files: bool = True
    accept_dirs: bool = True
    accept_others: bool = False
    existed_only: bool = True
    file_validator: IPathValidator = ChainValidator()
    dir_validator: IPathValidator = file_validator
    follow_symlinks: bool = True


class PathExpander:
    def __init__(self, start_info: PathExpanderStartInfo = None):
        self.start_info = start_info or PathExpanderStartInfo()

    def __make_path(self, path: str | Path) -> Path:
        path = Path(path)
        if not path.is_absolute():
            if self.start_info.anchor_point:
                path = self.start_info.anchor_point / path
            else:
                path = Path.cwd() / path
        return path.resoleve() if self.start_info.follow_symlinks else path

    def __pure_expand(self, path: str | Path):
        path = self.__make_path(path)
        yield path
        if (
            path.is_dir(follow_symlinks=self.start_info.follow_symlinks)
            and self.start_info.expand_subdir
        ):
            for p in path.iterdir():
                yield from self.__pure_expand(p)

    def __validate_path(self, path: Path) -> bool:
        if not path.exists():
            return not self.start_info.existed_only

        if path.is_file():
            if not self.start_info.accept_files:
                return False
            return self.start_info.file_validator.validate(path)

        if path.is_dir():
            if not self.start_info.accept_dirs:
                return False
            return self.start_info.dir_validator.validate(path)

        return self.start_info.accept_others

    def expand(self, paths: list[str | Path]):
        for p in paths:
            for res in self.__pure_expand(p):
                if self.__validate_path(res):
                    yield res
