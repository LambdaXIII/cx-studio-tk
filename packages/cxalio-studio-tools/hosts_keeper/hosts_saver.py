import subprocess
import sys, shutil
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import datetime
from cx_studio.text import random_string
from cx_studio.filesystem.path_expander import CmdFinder
from cx_studio import system
from collections.abc import Iterable
from .appenv import appenv


class HostsSaver:
    def __init__(
        self,
        target_hosts: Path | None = None,
        source_hosts: Path | Iterable[str] | None = None,
        pretending_mode: bool | None = None,
        backup_dir: Path | None = None,
    ):
        self.target_hosts = target_hosts or appenv.system_hosts_path()

        if source_hosts is None:
            self.source_hosts = appenv.temp_hosts
        elif isinstance(source_hosts, Path):
            self.source_hosts = source_hosts
        else:
            self.source_hosts = appenv.temp_dir / "customed_hosts_lines.txt"
            with self.source_hosts.open("w", encoding="utf-8") as f:
                f.writelines(source_hosts)

        self.pretending_mode = pretending_mode or appenv.context.pretending_mode
        self.backup_dir = backup_dir or (appenv.config_manager.config_dir / "backups")
        self._temp_dir: TemporaryDirectory | None = None

    @property
    def temp_dir(self) -> Path:
        if self._temp_dir is None:
            self._temp_dir = TemporaryDirectory()
        return Path(self._temp_dir.name)

    def __del__(self):
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

    def generate_backup_file_path(self) -> Path:
        name = datetime.now().strftime("%Y%m%d_%H%M%S") + random_string(5) + ".bak"
        return self.backup_dir / name

    def _generate_replace_script_pwsh(self, from_: Path, to_: Path) -> Path:
        script = self.temp_dir / "replace_hosts.ps1"
        with script.open("w", encoding="utf-8") as f:
            f.write(
                f'Copy-Item -Path "{from_.resolve()}" -Destination "{to_.resolve()}" -Force\n'
            )
        return script

    def _generate_replace_script_bash(self, from_: Path, to_: Path) -> Path:
        script = self.temp_dir / "replace_hosts.sh"
        with script.open("w", encoding="utf-8") as f:
            f.write(f'cp -f "{from_.resolve()}" "{to_.resolve()}"\n')
        return script

    def _generate_replace_script_auto(self, from_: Path, to_: Path) -> Path:
        if sys.platform.startswith("win"):
            return self._generate_replace_script_pwsh(from_, to_)
        else:
            return self._generate_replace_script_bash(from_, to_)

    def _run_replace_script(self, script: Path, as_admin: bool = False) -> bool:
        cmd = ["bash" if script.suffix == ".sh" else "pwsh"]
        cmd.append(script.resolve())

        if as_admin:
            appenv.whisper(f"目标文件无写入权限，正查找 sudo 命令...")
            sudo_cmd = CmdFinder().find("sudo")
            if sudo_cmd is None:
                appenv.say("[cx.error]sudo 命令未找到，将无法以管理员权限进行替换。")
                return False
            cmd.insert(0, sudo_cmd)

        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            appenv.say(f"Replace script failed, error: {e}")
            return False

    def _backup_target_hosts(self, target_hosts: Path) -> bool:
        if not target_hosts.exists():
            appenv.whisper(
                f"Target hosts file {target_hosts} does not exist, skip backup."
            )
            return True
        backup_file = self.generate_backup_file_path()
        try:
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(target_hosts, backup_file)
        except Exception as e:
            appenv.say(f"无法创建备份文件，错误：{e}")
            return False
        return True

    def _show_hosts_lines(self, hosts_file: Path) -> None:
        with hosts_file.open("r", encoding="utf-8") as f:
            for line in f.readlines():
                print(line.strip())

    def save(self, target: Path | None = None) -> bool:
        """
        保存 hosts 文件。

        :param target: 目标 hosts 文件路径，默认值为系统 hosts 文件。
        :return: 如果成功保存新文件则返回 True，否则返回 False。
        """
        target = target or self.target_hosts
        if self.pretending_mode:
            appenv.say(f"[cx.info]假装模式已开启，新的内容将输出到标准输出。")
            self._show_hosts_lines(self.source_hosts)
            return False

        backup_result = self._backup_target_hosts(target)
        if not backup_result:
            appenv.say(
                f"[cx.warning]目标文件已存在且无法备份，将直接输出生成的 hosts 内容。"
            )
            return False

        script = self._generate_replace_script_auto(self.source_hosts, target)
        as_admin = system.check_file_permission(target)
        run_result = self._run_replace_script(script, as_admin)
        if not run_result:
            appenv.say(f"[cx.warning]替换脚本执行失败，目标文件 {target} 未被修改。")
            self._show_hosts_lines(self.source_hosts)
            return False

        return True
