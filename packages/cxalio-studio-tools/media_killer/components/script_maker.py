import sys
from collections.abc import Iterable, Generator
from pathlib import Path

from cx_studio.utils import TextUtils
from cx_wealth import IndexedListPanel
from .mission import Mission
from ..appenv import appenv


class ScriptMaker:
    def __init__(self, missions: Iterable[Mission]):
        self.missions = missions
        self._make_dir = "mkdir" if sys.platform == "win32" else "mkdir -p"
        self._default_suffix = ".ps1" if sys.platform == "win32" else ".sh"

    def iter_lines(self) -> Generator[str]:
        folders = set()
        for mission in self.missions:
            output_folders = {
                x.parent.resolve() for x in mission.iter_output_filenames()
            }
            for output_folder in output_folders:
                if not output_folder.exists():
                    yield f"{self._make_dir} {TextUtils.auto_quote(str(output_folder.resolve()))}"
                    folders.add(output_folder)

            es = [mission.preset.ffmpeg]
            es.extend(mission.iter_arguments(quote_mode="auto"))
            yield " ".join(es)

    def save(self, filename: str | Path):
        filename = Path(filename)
        if filename.suffix == "":
            filename = filename.with_suffix(self._default_suffix)

        appenv.check_overwritable_file(filename)

        lines = []
        with open(filename, "w", encoding="utf-8") as f:
            for line in self.iter_lines():
                lines.append(line)
                f.write(line)
                f.write("\n")

        appenv.whisper(IndexedListPanel(lines, title=filename.name, max_lines=999))
        appenv.say("已保存脚本到：{}".format(filename))
