from click import Path
from pydantic import BaseModel, Field
import importlib.resources
import csv
from cx_studio.utils import PathUtils
from threading import Lock, Event


class FormatInfo(BaseModel):
    name: str
    extensions: list[str]
    load_params: dict[str, str] = Field(default_factory=dict)
    save_params: dict[str, str] = Field(default_factory=dict)

    @property
    def preferred_extension(self) -> str:
        return self.extensions[0] if self.extensions else ""


class FormatDB:
    __lock = Lock()
    __default_data_loaded = Event()

    __data: dict[str, FormatInfo] = {}

    @classmethod
    def _load_default_data(cls):
        with cls.__lock:
            if cls.__default_data_loaded.is_set():
                return
            default_content = importlib.resources.read_text(
                "jpegger.components", "formats.csv"
            )

            reader = csv.DictReader(
                default_content.splitlines(), ["NAME", "EXTENSIONS"]
            )
            for row in reader:
                name = row["NAME"].strip().upper()
                extensions = [
                    PathUtils.normalize_suffix(ext.strip().lower())
                    for ext in row["EXTENSIONS"].split(" ")
                ]
                info = FormatInfo(name=name, extensions=extensions)
                cls.__data[info.name] = info
            cls.__default_data_loaded.set()

    @classmethod
    def search_for_name(cls, name: str) -> FormatInfo | None:
        return cls.__data.get(name)

    @classmethod
    def search_for_extension(cls, extension: str) -> FormatInfo | None:
        extension = PathUtils.normalize_suffix(extension).lower()
        for info in cls.__data.values():
            if extension in info.extensions:
                return info
        return None

    @classmethod
    def search(cls, keyword: str) -> FormatInfo | None:
        if result := cls.search_for_name(keyword):
            return result
        if result := cls.search_for_extension(keyword):
            return result
        return None

    @classmethod
    def formats(cls) -> list[str]:
        return list(cls.__data.keys())

    @classmethod
    def acceptable_extensions(cls) -> list[str]:
        result = {ext for x in cls.__data.values() for ext in x.extensions}
        exts = list(result)
        exts.sort()
        return exts


FormatDB._load_default_data()
