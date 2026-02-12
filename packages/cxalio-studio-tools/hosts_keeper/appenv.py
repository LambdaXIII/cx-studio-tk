from typing import override
from cx_tools.app import IAppEnvironment, ConfigManager
from .appcontext import AppContext
from cx_wealth import rich_types as r
import signal
from collections.abc import Sequence
from pathlib import Path
import sys, os
from tempfile import TemporaryDirectory
import importlib.resources


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "HostsKeeper"
        self.app_version = "0.6.3.2"
        self.app_description = "根据配置文件更新 hosts"
        self.context = AppContext()

        self.config_manager = ConfigManager(self.app_name)
        self._temp_dir: TemporaryDirectory | None = None

    @override
    def start(self):
        self.show_banners()
        super().start()
        if self._temp_dir is None:
            self._temp_dir = TemporaryDirectory()
            appenv.whisper(f"临时目录已创建：{self.temp_dir}")

    @override
    def stop(self):
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None
            appenv.whisper(f"临时目录已删除：{self.temp_dir}")
        super().stop()

    @property
    def temp_dir(self) -> Path:
        if self._temp_dir is None:
            self._temp_dir = TemporaryDirectory()
        return Path(self._temp_dir.name)

    @property
    def temp_hosts(self) -> Path:
        return self.temp_dir / "hosts"

    def show_banners(self):
        banners = []
        banner_text = importlib.resources.read_text(__package__, "banner.txt")
        banners.append(r.Align.center(banner_text))
        banners.append(r.Align.center("你的 hosts 由我来守护！"))
        banners.append(r.Align.center("v" + self.app_version))
        group = r.Group(*banners)
        appenv.console.print(group, style="bold cyan", highlight=False)

    def is_debug_mode_on(self):
        return self.context.debug_mode

    def is_pretending_mode_on(self):
        return self.context.pretending_mode

    def load_arguments(self, arguments: Sequence[str] | None = None):
        self.context = AppContext.from_arguments(arguments)

    @staticmethod
    def system_hosts_path() -> Path:
        system = sys.platform

        # Windows 系统（包括 win32, cygwin 等）
        if system.startswith("win"):
            # 优先使用 SYSTEMROOT 环境变量（Windows 标准）
            system_root = os.environ.get(
                "SYSTEMROOT", os.environ.get("WINDIR", "C:\\Windows")
            )
            return Path(system_root) / "System32" / "drivers" / "etc" / "hosts"

        # Unix-like 系统（Linux, macOS, FreeBSD, Solaris 等）
        elif system.startswith(("linux", "darwin", "freebsd", "sunos")):
            return Path("/etc/hosts")

        # 兜底：其他类 Unix 系统通常也使用 /etc/hosts
        elif "bsd" in system or "unix" in system.lower():
            return Path("/etc/hosts")

        # 无法识别的操作系统
        raise NotImplementedError(
            f"Unsupported operating system: {system}. "
            "Please provide the hosts file path manually."
        )


appenv = AppEnv()

# signal.signal(signal.SIGINT, appenv.handle_interrupt)
