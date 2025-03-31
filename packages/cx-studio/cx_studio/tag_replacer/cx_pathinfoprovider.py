from pathlib import Path

from cx_studio.utils import NumberUtils


class PathInfoProvider:
    def __init__(self, path: str | Path):
        self.__path = Path(path)

    def __crop_path(self, level=1) -> list[str]:
        parts = self.__path.parts
        return parts[:-level] if level > 0 else []

    def __call__(self, params: str) -> str | None:
        params = [str(x) for x in params.split(" ")]

        key = params[0] if len(params) > 0 else "fullpath"
        param = params[1] if len(params) > 1 else None
        parent_level = NumberUtils.limit_number(param, min=1, cls=int) if param else 1

        match key:
            case "full":
                return str(self.__path.resolve())
            case "fullpath":
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
                return Path(*parts).resolve() if len(parts) > 0 else None
            case "parent_name":
                parts = self.__crop_path(parent_level)
                return parts[-1] if len(parts) > 0 else None
