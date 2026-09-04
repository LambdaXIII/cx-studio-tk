"""tag_replacer：模板标签占位符替换引擎子模块。

- TagPattern：占位符匹配模式（默认 ${key} / ${key:param}）
- TagReplacer：按「标签键 → provider」注册表展开占位符的替换器
- PathInfoProvider / StandardFolderProvider：常用 provider，分别输出
  指定路径的信息片段与系统标准文件夹位置
"""

from .path_info_provider import *
from .standard_folder_provider import *
from .tag_pattern import *
from .tag_replacer import *
