"""PathInfoProvider —— 路径信息片段 provider。

生成的可调用对象把一条路径解析为绝对路径、文件名、主干名、后缀、
上级目录等信息片段，常以 install_provider() 注册进 TagReplacer
（典型键如 source / target），供 ${key:信息键} 占位符展开。
"""

from collections.abc import Sequence
from pathlib import Path

from cx_studio.core import quick_clamp


class PathInfoProvider:
    """按需暴露指定路径各信息片段的可调用 provider。

    以空格分隔的参数字符串调用（如 "fullpath"、"parent"、"filename"），
    第一个词为信息键，支持的键及含义：

    - full / fullpath / absolute：resolve 后的绝对路径字符串
    - filename：文件名（含后缀）
    - complete_basename：主干名，保留内部点号（a.b.c.mp4 → a.b.c）
    - basename：主干名截至第一个点号（a.b.c.mp4 → a）
    - suffix：最后一个后缀，含点号（a.b.c.mp4 → .mp4）
    - complete_suffix：去掉首个后缀后的其余后缀拼接（→ .c.mp4）；
      无后缀时返回空串
    - parent：上级目录的绝对路径（路径不足一个父级时返回 None）
    - parent_name：上级目录的末段名称（路径不足一个父级时返回 None）

    未命中任何键时返回 None（键省略、拼写错误等均落于此）。参数中的
    第二个空格词本用于指定 parent / parent_name 的向上层级（默认 1 级），
    但当前实现会将其作为字符串送入 quick_clamp 触发类型比较错误
    （TypeError），实际只能使用默认 1 级，请勿传第二词。

    Args:
        path: 基准路径。相对路径以当前工作目录为锚点参与解析。
    """

    def __init__(self, path: str | Path):
        self.__path = Path(path)

    def __crop_path(self, level: int = 1) -> Sequence[str]:
        parts = self.__path.parts
        return parts[:-level] if level > 0 else []

    def __call__(self, params: str) -> str | None:
        pms = [str(x) for x in params.split(" ")]

        key = pms[0] if len(pms) > 0 else "fullpath"
        param = pms[1] if len(pms) > 1 else None
        parent_level = int(quick_clamp(param, bottom=1, cls=int) if param else 1)

        match key:
            case "full":
                return str(self.__path.resolve())
            case "fullpath":
                return str(self.__path.resolve())
            case "absolute":
                return str(self.__path.resolve())
            case "filename":
                return self.__path.name
            case "complete_basename":
                return self.__path.stem
            case "basename":
                stem = self.__path.stem
                return stem.split(".")[0] if "." in stem else stem
            case "suffix":
                return self.__path.suffix
            case "complete_suffix":
                suffixes = self.__path.suffixes
                if len(suffixes) > 1:
                    return "".join(suffixes[1:])
                return suffixes[0] if len(suffixes) > 0 else ""
            case "parent":
                parts = self.__crop_path(parent_level)
                return str(Path(*parts).resolve()) if len(parts) > 0 else None
            case "parent_name":
                parts = self.__crop_path(parent_level)
                return parts[-1] if len(parts) > 0 else None
