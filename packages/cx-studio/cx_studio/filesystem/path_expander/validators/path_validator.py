"""路径验证器的抽象契约与链式组合实现。

IPathValidator 定义以路径为输入、返回布尔判定的验证接口；
ChainValidator 将若干验证器按 AND 语义组合为一个验证器，
供 PathExpander 等消费方统一使用。
"""

from abc import ABC, abstractmethod
from pathlib import Path


class IPathValidator(ABC):
    """路径验证器的抽象基类（契约）。

    实现对给定的路径字符串/Path 返回布尔判定：True 表示路径通过
    验证（应被接受），False 表示未通过。具体验证器同时充当过滤器，
    常与 PathExpander 配合决定某个候选路径是否产出。子类必须实现
    validate()。
    """

    @abstractmethod
    def validate(self, path: str | Path) -> bool:
        """判断给定路径是否满足本验证器的条件。

        Args:
            path: 待验证的路径（字符串或 Path 对象）。

        Returns:
            True 表示路径通过验证，False 表示未通过。
        """
        pass


class ChainValidator(IPathValidator):
    """按 AND 语义链式组合多个验证器的验证器。

    内部按顺序维护一个验证器列表；validate() 要求链上所有验证器
    全部通过才返回 True（短路求值），空链恒为 True（不设任何限制）。
    install() / uninstall() 均返回 self，支持链式调用与就地修改。
    """

    def __init__(self, validators: list[IPathValidator] | None = None):
        """初始化验证器链。

        Args:
            validators: 初始验证器列表；None 时从空链开始。
        """
        self.__validators = validators or []

    def install(self, validator: IPathValidator):
        """将验证器追加到链尾。

        Args:
            validator: 要安装的验证器。

        Returns:
            self，便于链式调用（如 chain.install(a).install(b)）。
        """
        self.__validators.append(validator)
        return self

    def uninstall(self, validator: IPathValidator):
        """从链中移除指定的验证器。

        Args:
            validator: 要移除的验证器。

        Returns:
            self，便于链式调用。

        Raises:
            ValueError: 链中不存在该验证器时抛出（list.remove 语义）。
        """
        self.__validators.remove(validator)
        return self

    def validate(self, path: str | Path) -> bool:
        """判断路径是否通过链上全部验证器。

        空链恒返回 True；非空链对每个验证器短路求值 AND，
        任一验证器不通过即返回 False。

        Args:
            path: 待验证的路径（字符串或 Path 对象）。

        Returns:
            链上所有验证器都通过时为 True，否则为 False。
        """
        return (
            True
            if len(self.__validators) == 0
            else all(v.validate(path) for v in self.__validators)
        )
