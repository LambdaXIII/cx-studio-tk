"""PathExpander — 基于验证器配置的路径展开器。

将若干输入路径展开为满足过滤条件的 Path 序列：按需递归展开子目录，
再依据存在性、路径类型开关与自定义验证器逐项过滤。全部行为由嵌套的
StartInfo dataclass 配置。
"""

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable
from .validators.path_validator import IPathValidator, ChainValidator


class PathExpander:
    """将路径展开为通过验证的 Path 序列。

    展开流程（见 expand）：先把路径按 anchor_point 基准归一化为绝对
    路径；若为目录且 expand_subdir 开启，则以深度优先顺序产出目录
    自身及其全部后代；随后逐项执行过滤——先按 existed_only 决定是否
    要求路径真实存在，再按类型匹配 accept_files / accept_dirs /
    accept_others，文件与目录还须分别通过 file_validator /
    dir_validator 的判定。

    注意：
        - 目录是否继续向下展开只取决于其类型与 expand_subdir，与目录
          自身能否通过过滤无关（目录被拒收时其后代仍会被展开过滤）。
        - StartInfo.file_validator 与 dir_validator 的默认值指向同一个
          共享 ChainValidator 实例，通过该默认实例调用 install() /
          uninstall() 会同时影响二者；需要彼此独立时应显式赋入新实例。
    """

    @dataclass
    class StartInfo:
        """展开与过滤的全部配置项。

        Args:
            anchor_point: 相对输入路径的基准目录；None 时相对路径
                基于当前工作目录展开。
            expand_subdir: True 时递归展开目录的全部后代（深度优先）。
            accept_files: 是否接受（产出）文件。
            accept_dirs: 是否接受（产出）目录。
            accept_others: 是否接受既非文件也非目录的其他路径
                （如 FIFO、设备文件）。
            existed_only: True 时只接受真实存在的路径；False 时
                不存在的路径也可通过（前提是不被其他条件拦截）。
            file_validator: 对文件路径（字符串形式）判定的验证器，
                不通过则文件被过滤。
            dir_validator: 对目录路径（字符串形式）判定的验证器。
            follow_symlinks: True 时路径经 resolve() 解析符号链接
                并绝对化；False 时不做 resolve()。
        """

        anchor_point: Path | None = None
        expand_subdir: bool = True
        accept_files: bool = True
        accept_dirs: bool = True
        accept_others: bool = False
        existed_only: bool = True
        file_validator: IPathValidator = ChainValidator()
        dir_validator: IPathValidator = file_validator
        follow_symlinks: bool = True

    def __init__(self, start_info: "PathExpander.StartInfo | None" = None):
        self.start_info: PathExpander.StartInfo = start_info or PathExpander.StartInfo()

    def __make_path(self, path: str | Path) -> Path:
        path = Path(path)
        if not path.is_absolute():
            if self.start_info.anchor_point:
                path = self.start_info.anchor_point / path
            else:
                path = Path.cwd() / path
        return path.resolve() if self.start_info.follow_symlinks else path

    def __pure_expand(self, path: str | Path) -> Iterable[Path]:
        path = self.__make_path(path)
        yield path
        if (
            # path.is_dir(follow_symlinks=self.start_info.follow_symlinks)
            path.is_dir()
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
            return self.start_info.file_validator.validate(str(path))

        if path.is_dir():
            if not self.start_info.accept_dirs:
                return False
            return self.start_info.dir_validator.validate(str(path))

        return self.start_info.accept_others

    def expand(self, *paths: str | Path) -> Iterable[Path]:
        """展开一个或多个起点路径，产出通过全部过滤条件的路径。

        依次处理每个起点：目录在 expand_subdir=True 时按深度优先展开
        自身及全部后代，再对每个候选路径依次执行存在性、类型与
        验证器过滤；未通过过滤的路径不产出。

        Args:
            *paths: 一个或多个起点路径（文件或目录，str 或 Path）。

        Yields:
            满足 start_info 全部过滤条件的 Path；同一目录树的展开
            顺序为目录先于其子项，同层子项顺序与文件系统迭代顺序
            一致。
        """
        for p in paths:
            for res in self.__pure_expand(p):
                if self.__validate_path(res):
                    yield res
