import shutil
from hosts_keeper.i18n import _

import subprocess
import base64
import shlex
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from cx_studio import system
from cx_studio.system import CrossRunner, SystemType
from cx_studio.text import random_string
from .appenv import appenv
from cx_tools.app import IAppComponent, IAppEnvironment
from .appcontext import HostsKeeperContext

# elevated_replace: CrossRunner 实例，调用签名 (source, target) -> bool
# 已注册平台：LINUX(sudo/doas/pkexec), MACOS(sudo/osascript), WINDOWS(sudo/PowerShell UAC)
elevated_replace = CrossRunner()


@elevated_replace.for_system(SystemType.LINUX)
def _elevated_replace_linux(source: Path, target: Path) -> bool:
    """Linux 提权替换。

    尝试 sudo / doas / pkexec 替换，若均失败则回退。
    """
    # 尝试 sudo
    try:
        subprocess.run(
            ["sudo", "cp", str(source), str(target)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    # 尝试 doas
    try:
        subprocess.run(
            ["doas", "cp", str(source), str(target)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    # 尝试 pkexec
    try:
        subprocess.run(
            ["pkexec", "cp", str(source), str(target)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    return False


@elevated_replace.for_system(SystemType.MACOS)
def _elevated_replace_macos(source: Path, target: Path) -> bool:
    """macOS 提权替换。

    尝试 sudo / osascript 提权替换。
    """
    # 尝试 sudo
    try:
        subprocess.run(
            ["sudo", "cp", str(source), str(target)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    # 尝试 osascript 提权
    escaped_source = shlex.quote(str(source))
    escaped_target = shlex.quote(str(target))
    script = (
        f'do shell script "cp {escaped_source} {escaped_target}"'
        " with administrator privileges"
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    return False


@elevated_replace.for_system(SystemType.WINDOWS)
def _elevated_replace_windows(source: Path, target: Path) -> bool:
    """Windows 提权替换。

    尝试 sudo / PowerShell UAC 提权替换。
    """
    # 尝试 sudo（Windows 11+ 24H2）
    try:
        subprocess.run(
            ["sudo", "copy", "/Y", str(source), str(target)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    # 尝试 PowerShell UAC 提权
    encoded_source = base64.b64encode(source.as_posix().encode("utf-16-le")).decode(
        "ascii"
    )
    encoded_target = base64.b64encode(target.as_posix().encode("utf-16-le")).decode(
        "ascii"
    )
    ps_cmd = (
        f"$s = [System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('{encoded_source}'));"
        f"$t = [System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('{encoded_target}'));"
        "Copy-Item -Path $s -Destination $t -Force"
    )
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"Start-Process -Verb RunAs -Wait -FilePath 'powershell' -ArgumentList '-NoProfile', '-Command', '{ps_cmd}'",
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    return False


dns_flush = CrossRunner()


@dns_flush.for_system(SystemType.WINDOWS)
def _dns_flush_windows(skip_flush: bool = False) -> bool:
    """Windows: 刷新 DNS 缓存。

    使用 ipconfig /flushdns，若失败则提示手动命令。
    """
    if skip_flush:
        appenv.say(_("跳过 DNS 缓存刷新。请手动运行: ipconfig /flushdns"))
        return True

    try:
        subprocess.run(
            ["ipconfig", "/flushdns"],
            check=True,
            capture_output=True,
            timeout=10,
        )
        appenv.say(_("DNS 缓存已刷新。"))
        return True
    except subprocess.CalledProcessError:
        appenv.say(_("DNS 缓存刷新失败。请手动运行: ipconfig /flushdns"))
        return False
    except FileNotFoundError:
        appenv.say(_("未找到 ipconfig 命令。请手动刷新 DNS 缓存。"))
        return False


@dns_flush.for_system(SystemType.MACOS)
def _dns_flush_macos(skip_flush: bool = False) -> bool:
    """macOS: 刷新 DNS 缓存。

    使用 dscacheutil / killall mDNSResponder。
    """
    if skip_flush:
        appenv.say(
            _(
                "跳过 DNS 缓存刷新。请手动运行: sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
            )
        )
        return True

    try:
        subprocess.run(
            ["sudo", "dscacheutil", "-flushcache"],
            check=True,
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            ["sudo", "killall", "-HUP", "mDNSResponder"],
            check=True,
            capture_output=True,
            timeout=10,
        )
        appenv.say(_("DNS 缓存已刷新。"))
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        appenv.say(
            _(
                "DNS 缓存刷新失败。请手动运行: sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
            )
        )
        return False


@dns_flush.for_system(SystemType.LINUX)
def _dns_flush_linux(skip_flush: bool = False) -> bool:
    """Linux: 提示手动刷新 DNS 缓存，不自动执行命令。

    各发行版差异大，仅提示用户手动操作。
    """
    commands = [
        "sudo systemctl restart systemd-resolved",
        "sudo resolvectl flush-caches",
        "sudo service nscd restart",
        "sudo /etc/init.d/dnsmasq restart",
        "sudo systemctl restart NetworkManager",
    ]
    if skip_flush:
        appenv.say(_("跳过 DNS 缓存刷新。你可尝试以下命令之一: ") + "; ".join(commands))
    else:
        appenv.say(
            _("请手动刷新 DNS 缓存。你可尝试以下命令之一: ") + "; ".join(commands)
        )
    return False


class HostsSaver(IAppComponent):
    def __init__(
        self,
        appenv: IAppEnvironment,
        context: HostsKeeperContext,
        target_hosts: Path | None = None,
        source_hosts: Path | Iterable[str] | None = None,
        pretending_mode: bool | None = None,
        backup_dir: Path | None = None,
    ):
        super().__init__(appenv, context)
        self.appenv = appenv
        self.context = context
        self.target_hosts = target_hosts or context.system_hosts_path()

        if source_hosts is None:
            self.source_hosts = context.temp_hosts
        elif isinstance(source_hosts, Path):
            self.source_hosts = source_hosts
        else:
            # source_hosts 是 Iterable[str]，写入临时文件
            self.source_hosts = context.temp_hosts
            # 写入用 utf-8（不产生 BOM），系统 DNS 解析器不期望 BOM
            with self.source_hosts.open("w", encoding="utf-8") as f:
                f.writelines(source_hosts)

        self.pretending_mode = (
            pretending_mode if pretending_mode is not None else context.pretending_mode
        )
        self.backup_dir = backup_dir or (context.config_manager.config_dir / "backups")

    def generate_backup_file_path(self) -> Path:
        name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{random_string(5)}.bak"
        return self.backup_dir / name

    def _backup_target_hosts(self, target_hosts: Path) -> bool:
        if not target_hosts.exists():
            self.appenv.whisper(
                _("目标 hosts 文件 {path} 不存在，跳过备份。").format(path=target_hosts)
            )
            return True
        backup_file = self.generate_backup_file_path()
        try:
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(target_hosts, backup_file)
        except Exception as e:
            self.appenv.say(_("无法创建备份文件，错误：{error}").format(error=e))
            return False
        return True

    def _show_hosts_lines(self, hosts_file: Path) -> None:
        # 读取用 utf-8-sig 剥离可能的 BOM：
        #   URL 内容源等可能返回带 BOM 的数据，写入到 temp file 的编码为 utf-8（不产生 BOM），
        #   但 BOM 已在源数据中，写入时作为普通数据保留了下来。显示读取时必须剥离。
        # 写入保持 utf-8（系统 DNS 解析器不期望 BOM，强制不带 BOM）。
        with hosts_file.open("r", encoding="utf-8-sig") as f:
            for line in f:
                # 数据输出走 stdout（say/whisper 走 stderr），便于管道重定向
                print(line.strip())

    def save(self, target: Path | None = None) -> bool:
        """保存 hosts 文件。

        根据目标路径决定策略：
        - 系统 hosts 路径（与 `system_hosts_path()` 一致）：
          1. 备份原文件
          2. 已有管理员权限 → 直接 `shutil.copyfile`
          3. 无管理员权限 → 调用 `elevated_replace` 提权替换
        - 自定义路径（`-t` 参数）：直接 `shutil.copyfile`，不提权不备份，
          无权限时报错。
        - 假装模式：仅输出内容到标准输出，不执行任何文件操作。

        Args:
            target: 目标 hosts 文件路径，默认为系统 hosts 文件。

        Returns:
            True 表示成功保存，False 表示失败（失败时会输出内容作为手动备选）。
        """
        target = target or self.target_hosts
        if self.pretending_mode:
            self.appenv.say(
                f"[cx.info]{_('假装模式已开启，新的内容将输出到标准输出。')}"
            )
            self._show_hosts_lines(self.source_hosts)
            return False

        is_system_hosts = target.resolve() == self.context.system_hosts_path().resolve()

        if is_system_hosts:
            # 系统 hosts 路径：需要备份，可能需提权
            backup_result = self._backup_target_hosts(target)
            if not backup_result:
                self.appenv.say(
                    f"[cx.warning]{_('目标文件已存在且无法备份，将直接输出生成的 hosts 内容。')}"
                )
                self._show_hosts_lines(self.source_hosts)
                return False

            if system.is_user_admin():
                # 已有系统权限，直接替换
                try:
                    shutil.copyfile(self.source_hosts, target)
                    return True
                except OSError:
                    self.appenv.say(
                        f"[cx.error]{_('替换失败。目标文件 {path} 无法写入。').format(path=target)}"
                    )
                    return False
            else:
                # 需提权替换
                try:
                    ok = elevated_replace(self.source_hosts, target)
                    if not ok:
                        self._show_hosts_lines(self.source_hosts)
                    return ok
                except NotImplementedError:
                    self.appenv.say(
                        f"[cx.error]{_('当前平台不支持自动提权替换。请以管理员权限运行本程序。')}"
                    )
                    self._show_hosts_lines(self.source_hosts)
                    return False
        else:
            # 用户指定的自定义路径：不提权、不备份
            try:
                shutil.copyfile(self.source_hosts, target)
                return True
            except PermissionError:
                self.appenv.say(
                    f"[cx.error]{_('目标文件 {path} 没有写入权限。').format(path=target)}"
                )
                self.appenv.say(
                    f"[cx.error]{_('请自行处理目标文件的权限问题，或以管理员权限运行本程序。')}"
                )
                self._show_hosts_lines(self.source_hosts)
                return False
