"""text：文本处理子包。

汇聚三类文本能力：
- text_utils：通用字符串小工具（引用处理、随机字符串、列表归一、
  去换行等）
- shell_escape：Shell 命令行参数转义与拼接
- tag_replacer：模板标签占位符替换引擎及常用 provider（TagReplacer、
  PathInfoProvider、StandardFolderProvider）
"""

from . import tag_replacer

TagReplacer = tag_replacer.TagReplacer
PathInfoProvider = tag_replacer.PathInfoProvider


from .text_utils import *


from .shell_escape import *
