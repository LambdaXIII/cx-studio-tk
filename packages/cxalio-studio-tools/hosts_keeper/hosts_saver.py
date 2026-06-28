import shutil
from cx_tools.i18n import _

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

# elevated_replace: CrossRunner 实例，调用签名 (source, target) -> bool
# 已注册平台：LINUX(sudo/doas/pkexec), MACOS(sudo/osascript), WINDOWS(sudo/PowerShell UAC)
elevated_replace = CrossRunner()


@elevated_replace.for_system(SystemType.LINUX)
def _elevated_replace_linux(source: Path, target: Path) -> bool:
    """Linux 提权替换。

    检测顺序: sudo → doas → pkexec。`shutil.which()` 正向检测，
    找到第一个可用工具执行一次，不降级重试。

    Args:
        source: 新内容的文件路径。
        target: 目标 hosts 文件路径。

    Returns:
        True 表示替换成功，False 表示失败。
    """
    for tool in ("sudo", "doas", "pkexec"):
        if shutil.which(tool):
            break
    else:
        appenv.say(
            "[cx.error]当前平台未检测到可用的提权工具（sudo/doas/pkexec）。"
            "请安装 sudo 或以 root 运行本程序。"
        )
        return False

    try:
        subprocess.run(
            [tool, "cp", "-f", str(source.resolve()), str(target.resolve())],
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        appenv.say(f"[cx.error]{_('提权替换失败。')}[/]")
        return False


@elevated_replace.for_system(SystemType.MACOS)
def _elevated_replace_macos(source: Path, target: Path) -> bool:
    """macOS 提权替换。

    检测顺序: sudo → osascript（弹系统权限对话框）。
    终端用户走 sudo，桌面用户走 osascript GUI 授权。

    Args:
        source: 新内容的文件路径。
        target: 目标 hosts 文件路径。

    Returns:
        True 表示替换成功，False 表示失败。
    """
    if shutil.which("sudo"):
        try:
            subprocess.run(
                ["sudo", "cp", "-f", str(source.resolve()), str(target.resolve())],
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            appenv.say("[cx.error]提权替换失败。")
            return False

    if shutil.which("osascript"):
        cmd = shlex.join(["cp", "-f", str(source.resolve()), str(target.resolve())])
        script = f"do shell script {cmd} with administrator privileges"
        try:
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                timeout=120,
            )
            return True
        except subprocess.CalledProcessError:
            appenv.say("[cx.error]提权替换失败。")
            return False
        except subprocess.TimeoutExpired:
            appenv.say("[cx.error]提权替换超时：用户未在授权对话框中确认。")
            return False

    appenv.say(
        "[cx.error]当前平台未检测到可用的提权工具（sudo/osascript）。"
        "请安装 sudo 或以 root 运行本程序。"
    )
    return False


@elevated_replace.for_system(SystemType.WINDOWS)
def _elevated_replace_windows(source: Path, target: Path) -> bool:
    """Windows 提权替换。

    检测顺序: Win11 内置 sudo → PowerShell UAC（弹 UAC 对话框）。
    PowerShell 命令使用 -EncodedCommand + base64 编码，
    避免路径空格导致的 shell 转义问题。

    Args:
        source: 新内容的文件路径。
        target: 目标 hosts 文件路径。

    Returns:
        True 表示替换成功，False 表示失败。
    """
    # Win11 24H2+ 内置 sudo — 非致命，失败后回退到 PowerShell UAC
    sudo_attempted = False
    if shutil.which("sudo"):
        sudo_attempted = True
        try:
            subprocess.run(
                ["sudo", "cp", "-f", str(source.resolve()), str(target.resolve())],
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            appenv.whisper("[cx.warning]sudo 提权失败，尝试 PowerShell UAC...")

    # PowerShell UAC
    if shutil.which("powershell.exe"):
        ps_command = (
            f"Copy-Item -Path '{str(source.resolve())}' "
            f"-Destination '{str(target.resolve())}' -Force"
        )
        encoded = base64.b64encode(ps_command.encode("utf-16-le")).decode("ascii")
        try:
            subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    f"Start-Process powershell.exe -Verb RunAs -Wait"
                    f" -ArgumentList '-NoProfile','-EncodedCommand','{encoded}'",
                ],
                check=True,
                timeout=120,
            )
            return True
        except subprocess.CalledProcessError:
            appenv.say(f"[cx.error]{_('PowerShell UAC 提权替换失败。')}[/]")
            return False
        except (OSError, FileNotFoundError):
            pass
        except subprocess.TimeoutExpired:
            appenv.say("[cx.error]提权替换超时：用户未在 UAC 对话框中确认。")
            return False

    if sudo_attempted:
        appenv.say("[cx.error]所有提权方式均失败。请检查权限设置。")
    else:
        appenv.say(
            "[cx.error]当前平台未检测到可用的提权工具（sudo/powershell.exe）。"
            "请以管理员权限运行本程序。"
        )
    return False


dns_flush = CrossRunner()


@dns_flush.for_system(SystemType.WINDOWS)
def _dns_flush_windows(skip_flush: bool = False) -> bool:
    """Windows: 刷新 DNS 缓存。

    尝试直接执行 ipconfig /flushdns，无管理员权限时通过 PowerShell UAC 提权。

    Args:
        skip_flush: True 时仅给出命令提示，不执行刷新。
    """
    if skip_flush:
        appenv.say(
            "[cx.info]未刷新 DNS 缓存，请自行刷新。以管理员身份运行："
            "[bold]ipconfig /flushdns[/bold]"
        )
        return False

    # 优先直接尝试（可能已有管理员权限）
    try:
        subprocess.run(["ipconfig", "/flushdns"], check=True, timeout=30)
        appenv.say(f"[cx.success]{_('已刷新 DNS 缓存（ipconfig /flushdns）。')}[/]")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    # 通过 PowerShell UAC 提权执行
    if shutil.which("powershell.exe"):
        ps_command = "ipconfig /flushdns"
        encoded = base64.b64encode(ps_command.encode("utf-16-le")).decode("ascii")
        try:
            subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    f"Start-Process powershell.exe -Verb RunAs -Wait"
                    f" -ArgumentList '-NoProfile','-EncodedCommand','{encoded}'",
                ],
                check=True,
                timeout=60,
            )
            appenv.say("[cx.success]已刷新 DNS 缓存（ipconfig /flushdns）。")
            return True
        except subprocess.CalledProcessError:
            pass
        except (OSError, FileNotFoundError):
            pass
        except subprocess.TimeoutExpired:
            appenv.say("[cx.error]DNS 缓存刷新超时。")
            return False

    appenv.say(
        "[cx.warning]未能自动刷新 DNS 缓存。"
        "请以管理员身份运行：[bold]ipconfig /flushdns[/bold]"
    )
    return False


@dns_flush.for_system(SystemType.MACOS)
def _dns_flush_macos(skip_flush: bool = False) -> bool:
    """macOS: 刷新 DNS 缓存。

    dscacheutil 刷新 Directory Service 缓存（无需 sudo），
    sudo killall -HUP mDNSResponder 刷新 mDNSResponder（需提权）。

    Args:
        skip_flush: True 时仅给出命令提示，不执行刷新。
    """
    if skip_flush:
        appenv.say(
            "[cx.info]未刷新 DNS 缓存，请自行刷新。手动执行："
            "[bold]sudo killall -HUP mDNSResponder[/bold]"
        )
        return False

    try:
        subprocess.run(["dscacheutil", "-flushcache"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass  # 非关键步骤，忽略失败

    try:
        subprocess.run(
            ["sudo", "killall", "-HUP", "mDNSResponder"],
            check=True,
            timeout=60,
        )
        appenv.say("[cx.success]已刷新 DNS 缓存。")
        return True
    except subprocess.CalledProcessError:
        appenv.say(
            "[cx.warning]DNS 缓存刷新失败。请手动执行："
            "[bold]sudo killall -HUP mDNSResponder[/bold]"
        )
        return False
    except subprocess.TimeoutExpired:
        appenv.say(
            "[cx.warning]DNS 缓存刷新超时。请手动执行："
            "[bold]sudo killall -HUP mDNSResponder[/bold]"
        )
        return False


@dns_flush.for_system(SystemType.LINUX)
def _dns_flush_linux(skip_flush: bool = False) -> bool:
    """Linux: 提示手动刷新 DNS 缓存，不自动执行命令。

    Args:
        skip_flush: True 时仅给出命令提示，不执行刷新。
    """
    if skip_flush:
        appenv.say(
            "[cx.info]未刷新 DNS 缓存，请自行刷新。可尝试：\n"
            "  sudo systemctl restart systemd-resolved   # systemd-resolved\n"
            "  sudo systemctl restart nscd               # nscd\n"
            "  sudo systemctl restart dnsmasq             # dnsmasq"
        )
        return False

    appenv.say(
        "[cx.info]hosts 文件已更新。如需刷新 DNS 缓存，请手动执行：\n"
        "  sudo systemctl restart systemd-resolved   # systemd-resolved\n"
        "  sudo systemctl restart nscd               # nscd\n"
        "  sudo systemctl restart dnsmasq             # dnsmasq"
    )
    return False


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
            # 写入用 utf-8（不产生 BOM），系统 DNS 解析器不期望 BOM
            with self.source_hosts.open("w", encoding="utf-8") as f:
                f.writelines(source_hosts)

        self.pretending_mode = pretending_mode or appenv.context.pretending_mode
        self.backup_dir = backup_dir or (appenv.config_manager.config_dir / "backups")

    def generate_backup_file_path(self) -> Path:
        name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{random_string(5)}.bak"
        return self.backup_dir / name

    def _backup_target_hosts(self, target_hosts: Path) -> bool:
        if not target_hosts.exists():
            appenv.whisper(
                _("目标 hosts 文件 {path} 不存在，跳过备份。").format(path=target_hosts)
            )
            return True
        backup_file = self.generate_backup_file_path()
        try:
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(target_hosts, backup_file)
        except Exception as e:
            appenv.say(_("无法创建备份文件，错误：{error}").format(error=e))
            return False
        return True

    def _show_hosts_lines(self, hosts_file: Path) -> None:
        # 读取用 utf-8-sig 剥离可能的 BOM：
        #   URL 内容源等可能返回带 BOM 的数据，写入到 temp file 的编码为 utf-8（不产生 BOM），
        #   但 BOM 已在源数据中，写入时作为普通数据保留了下来。显示读取时必须剥离。
        # 写入保持 utf-8（系统 DNS 解析器不期望 BOM，强制不带 BOM）。
        with hosts_file.open("r", encoding="utf-8-sig") as f:
            for line in f:
                appenv.console.print(line.strip())

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
            appenv.say(f"[cx.info]假装模式已开启，新的内容将输出到标准输出。")
            self._show_hosts_lines(self.source_hosts)
            return False

        is_system_hosts = target.resolve() == appenv.system_hosts_path().resolve()

        if is_system_hosts:
            # 系统 hosts 路径：需要备份，可能需提权
            backup_result = self._backup_target_hosts(target)
            if not backup_result:
                appenv.say(
                    f"[cx.warning]目标文件已存在且无法备份，将直接输出生成的 hosts 内容。"
                )
                self._show_hosts_lines(self.source_hosts)
                return False

            if system.is_user_admin():
                # 已有系统权限，直接替换
                try:
                    shutil.copyfile(self.source_hosts, target)
                    return True
                except OSError:
                    appenv.say(f"[cx.error]替换失败。目标文件 {target} 无法写入。")
                    return False
            else:
                # 需提权替换
                try:
                    ok = elevated_replace(self.source_hosts, target)
                    if not ok:
                        self._show_hosts_lines(self.source_hosts)
                    return ok
                except NotImplementedError:
                    appenv.say(
                        "[cx.error]当前平台不支持自动提权替换。请以管理员权限运行本程序。"
                    )
                    self._show_hosts_lines(self.source_hosts)
                    return False
        else:
            # 用户指定的自定义路径：不提权、不备份
            try:
                shutil.copyfile(self.source_hosts, target)
                return True
            except PermissionError:
                appenv.say(
                    f"[cx.error]目标文件 [filepath]{target}[/filepath] 没有写入权限。"
                )
                appenv.say(
                    "[cx.info]请自行处理目标文件的权限问题，或以管理员权限运行本程序。"
                )
                self._show_hosts_lines(self.source_hosts)
                return False
