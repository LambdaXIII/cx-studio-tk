"""ExecutableValidator — 可执行路径判定验证器。

基于 path_utils.is_executable 判断路径是否真实存在且对当前用户
可执行。
"""

from pathlib import Path

from .path_validator import IPathValidator
from ...path_utils import is_executable


class ExecutableValidator(IPathValidator):
    """判定路径是否存在且可执行的验证器。

    直接委托 path_utils.is_executable：路径真实存在且通过
    os.access(…, os.X_OK) 检查即视为可执行。注意该判定不区分
    文件与目录（目录通常也具备执行权限）。
    """

    def validate(self, path):
        """判断给定路径是否可执行。

        Args:
            path: 待验证的路径（字符串或 Path 对象）。

        Returns:
            路径存在且可执行时为 True，否则为 False。
        """
        path = Path(path)
        return is_executable(path)
