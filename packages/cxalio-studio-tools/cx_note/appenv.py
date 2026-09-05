"""CxNote 全局应用环境。

`CxNoteEnv` 继承 `IAppEnvironment`，提供 Rich 控制台、debug 输出门控，
并在构造时叠加 `cx.note.*` 专属样式（push_theme，无需在 cx_wealthy
默认主题中注册）。
"""

from cx_tools.app import IAppEnvironment
from cx_wealthy import rich_types as r

from . import __version__

CX_NOTE_STYLES: dict[str, str] = {
    "cx.note.section": "bold",
    "cx.note.done": "dim",
    "cx.note.id": "bold on grey15",
    "cx.note.hint": "dim",
}


class CxNoteEnv(IAppEnvironment):
    """CxNote 应用环境单例。"""

    app_name: str
    app_version: str

    def __init__(self):
        super().__init__()
        self.console.push_theme(r.Theme(CX_NOTE_STYLES))
        self.app_name = "CxNote"
        self.app_version = __version__


appenv = CxNoteEnv()
