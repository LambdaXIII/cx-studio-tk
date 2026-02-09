from .appenv import appenv
from pathlib import Path
from cx_studio.utils import TextUtils
from datetime import datetime
import shutil
from collections.abc import Iterable


class HostsSaver:
    def __init__(
        self,
        hosts_file_path: Path | None = None,
        pretending_mode: bool | None = None,
        backup_dir: Path | None = None,
    ):
        self.hosts_file_path = hosts_file_path or appenv.system_hosts_path()
        self.pretending_mode = pretending_mode or appenv.context.pretending_mode
        self.backup_dir = backup_dir or (appenv.config_manager.config_dir / "backups")

    def generate_backup_file_path(self) -> Path:
        name = (
            datetime.now().strftime("%Y%m%d_%H%M%S")
            + TextUtils.random_string(5)
            + ".bak"
        )
        return self.backup_dir / name

    def __overwrite_hosts(
        self, lines: Iterable[str], backup_file_path: Path | None = None
    ):
        if self.hosts_file_path.exists():
            backup = backup_file_path or self.generate_backup_file_path()
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.hosts_file_path, backup)

        with self.hosts_file_path.open("w") as f:
            f.writelines(lines)

    def __show_new_hosts(self, lines: Iterable[str]):
        for line in lines:
            print(line.strip())

    def save_to(self, lines: Iterable[str]) -> bool:
        try:
            if self.pretending_mode:
                self.__show_new_hosts(lines)
                return False
            else:
                self.__overwrite_hosts(lines)
                return True
        except Exception:
            return False
