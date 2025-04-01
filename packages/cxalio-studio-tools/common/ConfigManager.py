from pathlib import Path
import datetime
from cx_studio.utils import TextUtils


class ConfigManager:
    def __init__(self, app_name: str):
        self.app_name = app_name.strip()

    @property
    def config_dir(self):
        return Path.home() / ".config" / self.app_name

    @property
    def log_dir(self):
        return self.config_dir / "logs"

    def new_log_file(self):
        filename = f"{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}_{TextUtils.random_string(5)}.log"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        return self.log_dir / filename
