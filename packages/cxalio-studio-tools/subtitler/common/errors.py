"""字幕格式错误。

本模块定义格式框架唯一的错误类型：格式实现在解析来源与组织输出时的失败
统一以 FormatError 表达，并可选携带来源位置，便于调用方定位到具体行列。
"""


class FormatError(Exception):
    """字幕格式操作失败，可携带来源位置。

    来源不符合格式语法、编码无法判定、输出目标冲突等失败一律以本类型抛出，
    不静默跳过、不部分返回。消息只承载技术细节（原样可读），用户面提示由
    调用方在展示层组合。

    Attributes:
        message: 失败的技术描述。
        line: 出错的来源行号（从 1 起）；无行级位置时为 None。
        column: 出错的来源列号（从 1 起）；无列级位置时为 None。
    """

    def __init__(
        self,
        message: str,
        *,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        """初始化错误实例。

        Args:
            message: 失败的技术描述。
            line: 出错的来源行号（从 1 起），不适用时传 None。
            column: 出错的来源列号（从 1 起），不适用时传 None。
        """
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        """返回附带位置信息的错误描述。

        位置以「（第 <line> 行，第 <column> 列）」追加在消息之后；只知其一
        时只呈现存在的一方，两者皆缺时与 message 相同。

        Returns:
            str: 面向技术阅读者的错误描述。
        """
        if self.line is None and self.column is None:
            return self.message
        if self.line is not None and self.column is not None:
            position = f"（第 {self.line} 行，第 {self.column} 列）"
        elif self.line is not None:
            position = f"（第 {self.line} 行）"
        else:
            position = f"（第 {self.column} 列）"
        return f"{self.message}{position}"
