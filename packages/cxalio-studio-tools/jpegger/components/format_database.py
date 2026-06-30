"""图像格式数据库。

`FormatDB` 负责从内置 CSV 加载受支持的图像格式信息，并在运行时
提供按名称、扩展名查询的能力。`FormatInfo` 中的 `load_params` 与
`save_params` 字段作为扩展点，未来可由 `FormatDB.register()` 注册
自定义格式时填充。
"""

import csv
from dataclasses import dataclass, field
from importlib.resources import files
from threading import Event, Lock

from cx_studio.filesystem import normalize_suffix


@dataclass(frozen=True)
class FormatInfo:
    """单一图像格式的元信息。

    Args:
        name: 格式名称，统一为大写（如 "JPEG"、"PNG"）。
        extensions: 该格式支持的扩展名列表（带点，小写）。
        load_params: 透传给 `Image.open()` 的额外参数。
        save_params: 透传给 `Image.save()` 的额外参数。
    """

    name: str
    extensions: list[str]
    load_params: dict[str, str] = field(default_factory=dict)
    save_params: dict[str, str] = field(default_factory=dict)

    @property
    def preferred_extension(self) -> str:
        """返回首选扩展名（extensions 第一个元素）。"""
        return self.extensions[0] if self.extensions else ""


class FormatDB:
    """图像格式数据库。

    内部以名称大写作为键，首次查询时自动从 `formats.csv` 加载默认数据。
    支持通过 `register()` 在运行时追加或覆盖格式信息。
    """

    __lock = Lock()
    __default_data_loaded = Event()

    __data: dict[str, FormatInfo] = {}

    @classmethod
    def _load_default_data(cls) -> None:
        """从包内 `formats.csv` 加载默认格式数据（幂等）。"""
        with cls.__lock:
            if cls.__default_data_loaded.is_set():
                return
            default_content = (files("jpegger.components") / "formats.csv").read_text(
                encoding="utf-8"
            )

            reader = csv.DictReader(
                default_content.splitlines(), ["NAME", "EXTENSIONS"]
            )
            for row in reader:
                name = row["NAME"].strip().upper()
                extensions = [
                    normalize_suffix(ext.strip().lower())
                    for ext in row["EXTENSIONS"].split(" ")
                ]
                info = FormatInfo(name=name, extensions=extensions)
                cls.__data[info.name] = info
            cls.__default_data_loaded.set()

    @classmethod
    def register(cls, info: FormatInfo) -> None:
        """注册自定义格式信息，同名旧条目会被覆盖。

        Args:
            info: 要注册的 `FormatInfo` 实例。
        """
        cls._load_default_data()
        with cls.__lock:
            cls.__data[info.name] = info

    @classmethod
    def search_for_name(cls, name: str) -> FormatInfo | None:
        """按格式名称精确查询（不区分大小写）。"""
        cls._load_default_data()
        return cls.__data.get(name.upper())

    @classmethod
    def search_for_extension(cls, extension: str) -> FormatInfo | None:
        """按扩展名查询。"""
        cls._load_default_data()
        extension = normalize_suffix(extension).lower()
        for info in cls.__data.values():
            if extension in info.extensions:
                return info
        return None

    @classmethod
    def search(cls, keyword: str) -> FormatInfo | None:
        """先按名称查询，再按扩展名查询。"""
        cls._load_default_data()
        if result := cls.search_for_name(keyword):
            return result
        if result := cls.search_for_extension(keyword):
            return result
        return None

    @classmethod
    def formats(cls) -> list[str]:
        """返回所有已加载格式名称列表。"""
        cls._load_default_data()
        return list(cls.__data.keys())

    @classmethod
    def acceptable_extensions(cls) -> list[str]:
        """返回所有已知扩展名（去重、排序）。"""
        cls._load_default_data()
        result = {ext for x in cls.__data.values() for ext in x.extensions}
        exts = list(result)
        exts.sort()
        return exts
