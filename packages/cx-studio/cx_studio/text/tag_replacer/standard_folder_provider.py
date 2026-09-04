"""StandardFolderProvider —— 标准文件夹 provider。

生成的可调用对象把标签占位符展开为系统标准文件夹位置（用户主目录、
临时目录等），常以 install_provider() 注册进 TagReplacer 使用。
"""

import tempfile
from pathlib import Path


class StandardFolderProvider:
    """返回系统标准文件夹位置的可调用 provider。

    以空格分隔的参数字符串调用（如 "home"、"temp Downloads"）：
    第一个词为文件夹键，其后各词依次拼接为其下的子目录：

    - home：用户主目录（Path.home()）
    - temp：系统临时目录（tempfile.gettempdir()）
    - 其余未识别键：回退到当前工作目录（Path.cwd()）

    子目录拼接对以上分支均生效，返回前经 resolve() 归一为绝对路径。

    注意：__call__ 的 params 为必填形参；经 TagReplacer 使用时请让
    占位符携带参数部分（如 ${std:home}）——无参数的占位符会触发无参
    调用并抛 TypeError。
    """

    def __init__(self):
        pass

    def __call__(self, params: str) -> str | None:
        pms = [str(x) for x in params.split(" ")]
        key = pms[0] if len(pms) > 0 else "home"
        subfolders = pms[1:] if len(pms) > 1 else []

        result = Path.cwd().resolve()
        match key:
            case "home":
                result = Path.home()
            case "temp":
                result = Path(tempfile.gettempdir())

        if len(subfolders) > 0:
            result = Path(result, *subfolders)
        return str(result.resolve())
