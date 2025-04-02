import datetime
from pathlib import Path

from cx_studio.utils import text_utils


class ConfigManager:
    def __init__(self, app_name: str):
        self.app_name = app_name.strip()

    @property
    def config_dir(self) -> Path:
        return Path.home() / ".config" / self.app_name

    @property
    def log_dir(self) -> Path:
        return self.config_dir / "logs"

    def new_log_file(self):
        filename = f"{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}_{text_utils.random_string(5)}.log"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        return self.log_dir / filename

    def remove_old_log_files(self, keep=10):
        log_files = list(self.log_dir.glob("*.log"))
        log_files.sort(key=lambda x: x.stat().st_mtime)
        if len(log_files) > keep:
            for file in log_files[:-keep]:
                file.unlink()

    def get_file(self, filename: str) -> Path:
        return self.config_dir / filename
