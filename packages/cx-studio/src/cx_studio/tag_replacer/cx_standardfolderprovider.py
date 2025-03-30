from pathlib import Path
import tempfile


class StandardFolderProvider:
    def __init__(self):
        pass

    def __call__(self, params: str) -> str | None:
        params = [str(x) for x in params.split(" ")]
        key = params[0] if len(params) > 0 else "home"
        subfolders = params[1:] if len(params) > 1 else []

        result = Path.cwd().resolve()
        match key:
            case "home":
                result = Path.home()
            case "temp":
                result = tempfile.gettempdir()

        if len(subfolders) > 0:
            result = Path(result, *subfolders)
        return result.resolve()
