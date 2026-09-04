"""EmptyDirValidator — 空/非空目录判定验证器。

路径必须是真实存在的目录才会参与空判定；非目录路径一律判否。
"""

from pathlib import Path

from .path_validator import IPathValidator


class EmptyDirValidator(IPathValidator):
    """判定路径是否为（非）空目录的验证器。

    只有真实存在的目录才会进入空/非空判定：目录内没有任何条目
    （iterdir() 为空）视为空目录。reverse=False（默认）要求目录为
    空，reverse=True 要求目录非空；无论 reverse 取值，路径不是
    目录（含不存在）时一律返回 False。
    """

    def __init__(self, reverse=False):
        """初始化空目录验证器。

        Args:
            reverse: False 时验证目录“为空”，True 时验证目录
                “非空”。
        """
        self.__reverse = reverse

    def validate(self, path: str | Path) -> bool:
        """判断路径是否为空（或非空）目录。

        Args:
            path: 待验证的路径。

        Returns:
            路径为目录且空/非空状态与 reverse 配置一致时为 True；
            路径不是目录时恒为 False。
        """
        path = Path(path)
        if not path.is_dir():
            return False
        is_empty = len(list(path.iterdir())) == 0
        return not is_empty if self.__reverse else is_empty
