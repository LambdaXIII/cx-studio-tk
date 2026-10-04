"""字幕格式读向契约。

SubtitleLoader 是格式侧「来源 → Item」的抽象基类：一个 Loader 代表一种字幕
格式的读取实现，自带全部 IO 与语法知识，框架不介入其执行，也不持有任何
格式知识。
"""

from abc import ABC, abstractmethod
from pathlib import Path

from .model import SubtitleItem


class SubtitleLoader(ABC):
    """字幕格式读向：从来源提取 Item 列表。

    子类契约：

    - **自主 IO**：读文件、判定编码（``cx_studio.filesystem.detect_file_encoding``）、
      解码与语法解析全部由 Loader 自己完成。编码探测不出结论或解码失败时
      抛 FormatError，不猜测、不静默降级。来源入口是单个文件路径，一次导入
      涉及的文件数由格式规范决定——格式需要时，Loader 可以为一个入口自行
      读取其关联文件，无需框架参与。
    - **忠实提取**：按格式语义原样产出，不重排、不丢弃、不改写来源内容；
      来源中合法但罕见的结构（如交叠、乱序、超长文本）照实产出，如何消化
      由调用方决定。
    - **严格语法**：不符合本格式语法的来源抛 FormatError 并尽可能带上行/列
      位置，不静默跳过、不部分返回。
    - **扩展字段**：模型未定义而来源中存在的格式特有信息写入 Item 的扩展位，
      键统一带格式前缀（如 ``ttml_``），避免不同格式的键相撞；读写对称由
      格式实现自行保证。
    - **对容器一无所知**：接口只涉及 Item 与来源路径，不感知也不产出序列/
      工程等任何容器——容器由调用方在提取之后自行组织。
    - **时间模式自持**：本格式的时间表示模式是实现内部的常量，解析经共享的
      TimeCodec 完成，不进入任何跨组件接口。
    """

    @abstractmethod
    def load(self, path: Path) -> list[SubtitleItem]:
        """从来源提取全部 Item。

        Args:
            path: 来源文件路径。

        Returns:
            list[SubtitleItem]: 依来源出现顺序排列的 Item 列表；来源不含
                条目时为空列表。

        Raises:
            FormatError: 来源不符合本格式的语法，或编码无法判定/解码失败。
            OSError: 来源不可读等系统级失败。
        """
        pass
