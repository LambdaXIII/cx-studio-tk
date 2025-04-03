import tempfile
from pathlib import Path


class StandardFolderProvider:
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
