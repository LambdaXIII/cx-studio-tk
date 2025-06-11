from pydantic import BaseModel, Field


class FormatInfo(BaseModel):
    name: str
    extensions: list[str]
    load_params: dict[str, str] = Field(default_factory=dict)
    save_params: dict[str, str] = Field(default_factory=dict)


class FormatDB:
    def __init__(self) -> None:
        self._data: dict[str, FormatInfo] = {}
