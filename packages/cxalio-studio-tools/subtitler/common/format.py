"""字幕格式身份对象。

把一种格式的名称、所认扩展名与其读/写实现打包为不可变值对象：框架与模型
只认识 Format 与 Loader/Saver 契约，不认识任何具体格式，新增格式只需实现
双向契约并以 Format 打包，再在装配层登记。
"""

from dataclasses import dataclass

from .loader import SubtitleLoader
from .saver import SubtitleSaver


@dataclass(frozen=True)
class Format:
    """一种字幕格式的身份：名称、扩展名与双向实现。

    扩展名是装配层按文件后缀选择格式的依据，故以不含点号的小写形式登记
    （如 ``("srt",)``），查表前对目标后缀的归一（去点、转小写）由装配层
    负责。

    Attributes:
        name: 格式名称，用于展示与报错，如 ``"SubRip"``。
        extensions: 所认文件扩展名元组，不含点号，如 ``("srt",)``。
        loader: 读向实现。
        saver: 写向实现。
    """

    name: str
    extensions: tuple[str, ...]
    loader: SubtitleLoader
    saver: SubtitleSaver
