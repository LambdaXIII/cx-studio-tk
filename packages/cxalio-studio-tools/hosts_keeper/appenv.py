from cx_tools.app import IAppEnvironment, ConfigManager
from .appcontext import AppContext
from cx_wealth import rich_types as r
import signal
from collections.abc import Sequence
from pathlib import Path
import sys, os


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "HostsKeeper"
        self.app_version = "0.6.2"
        self.app_description = "根据配置文件更新 hosts"
        self.context = AppContext()

        self.config_manager = ConfigManager(self.app_name)

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
