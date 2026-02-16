import os
from pathlib import Path

from . import platform


def is_user_admin() -> bool:
    """检查当前用户是否为管理员"""
    try:
        if platform.current_os == platform.SystemType.WINDOWS:
            import ctypes

            # Windows: 调用 shell32.IsUserAnAdmin (需 ctypes)
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Linux/macOS/WSL: 检查有效用户ID是否为0 (root)
            return os.geteuid() == 0
    except:
        # 安全兜底：任何异常均视为无权限（避免程序崩溃）
        return False


def check_file_permission(path: os.PathLike | None = None, mode=os.W_OK) -> bool:
    """检查路径是否有写入权限"""
    if path is None:
        return False
    path = Path(path)
    if path.exists():
        return os.access(path, mode)
    return check_file_permission(path.parent, mode)
