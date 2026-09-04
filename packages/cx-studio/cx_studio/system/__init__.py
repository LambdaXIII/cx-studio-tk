"""system：系统抽象子包。

提供平台无关的系统能力抽象：
- platform：平台类型枚举与当前平台检测（SystemType、current_os）
- cross_runner：按系统类型注册 / 分派执行函数的注册表（CrossRunner）
- opener：跨平台「用系统默认程序打开」（system_open）
- permission_utils：管理员身份与文件权限检测
"""

from .cross_runner import *
from .opener import *
from .permission_utils import *
from .platform import *
