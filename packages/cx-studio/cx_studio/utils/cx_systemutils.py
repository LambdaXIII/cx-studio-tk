import subprocess, os, sys
from pathlib import Path
import ctypes


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
