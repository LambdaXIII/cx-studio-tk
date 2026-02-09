import subprocess, os, sys
from pathlib import Path
import ctypes
import platform


def is_user_admin() -> bool:
    """检查当前用户是否为管理员"""
    try:
        if sys.platform == "win32":
            # Windows: 调用 shell32.IsUserAnAdmin (需 ctypes)
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Linux/macOS/WSL: 检查有效用户ID是否为0 (root)
            return os.geteuid() == 0
    except Exception:
        # 安全兜底：任何异常均视为无权限（避免程序崩溃）
        return False


def open(path: Path) -> bool:
    """打开文件"""
    if not path.exists():
        return False
    try:
        if sys.platform.startswith("win"):  # Windows
            os.startfile(str(path))  # 仅Windows支持，自动处理文件/文件夹
        elif sys.platform.startswith("darwin"):  # macOS
            subprocess.Popen(
                ["open", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        else:  # Linux / BSD 等
            subprocess.Popen(
                ["xdg-open", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        return True
    except Exception:
        return False


def flush_dns_cache() -> bool:
    """
    跨平台刷新 DNS 缓存
    返回: True 表示至少一个刷新命令成功执行；False 表示全部失败
    """
    system = platform.system().lower()
    cmds = []

    # === 命令定义（按系统分类）===
    if system == "windows":
        cmds = [["ipconfig", "/flushdns"]]
    elif system == "darwin":  # macOS
        # 兼容新旧版本 macOS
        cmds = [
            ["killall", "-HUP", "mDNSResponder"],
            ["dscacheutil", "-flushcache"],  # 辅助命令（部分旧版本需要）
        ]
    elif system == "linux":
        # 按优先级尝试常见 DNS 缓存服务刷新方式
        cmds = [
            ["systemd-resolve", "--flush-caches"],  # systemd-resolved (Ubuntu 18.04+)
            ["resolvectl", "flush-caches"],  # systemd-resolved 新命令 (Ubuntu 20.04+)
            ["systemctl", "restart", "nscd"],  # Name Service Cache Daemon
            ["systemctl", "restart", "dnsmasq"],  # dnsmasq 服务
            ["service", "nscd", "restart"],  # 旧式 init 系统
            ["service", "dnsmasq", "restart"],
        ]
    else:
        print(f"❌ 不支持的操作系统: {system} ({platform.platform()})")
        return False

    # === 执行命令（尝试直到成功）===
    for cmd in cmds:
        try:
            # 捕获输出避免终端污染，设置超时防止卡死
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True,
            )
            if result.returncode == 0:
                print(f"✅ DNS 缓存刷新成功 ({' '.join(cmd)})")
                return True
            # 非关键错误继续尝试下一命令（Linux 多服务场景）
            if system != "linux":
                continue
        except (PermissionError, subprocess.CalledProcessError) as e:
            # 权限错误单独提示（关键路径）
            if "permission" in str(e).lower() or isinstance(e, PermissionError):
                print(
                    f"⚠️  权限不足: 请尝试用管理员权限运行（Windows: 右键'以管理员身份运行'；macOS/Linux: sudo python script.py）"
                )
                return False
        except FileNotFoundError:
            continue  # 命令不存在，尝试下一个
        except subprocess.TimeoutExpired:
            print(f"⚠️  命令超时: {' '.join(cmd)}")
            continue
        except Exception as e:
            print(f"⚠️  执行 '{' '.join(cmd)}' 时出错: {type(e).__name__}: {e}")
            continue

    # === 全部失败后的提示 ===
    # if system == "linux":
    #     print("ℹ️  提示: 多数 Linux 发行版默认无本地 DNS 缓存，刷新可能非必需。")
    #     print(
    #         "   若使用了 systemd-resolved/nscd/dnsmasq 等服务，请确认服务状态或手动刷新。"
    #     )
    # else:
    #     print(f"❌ DNS 刷新失败。请检查权限或手动执行系统命令。")
    return False
