"""cx_studio.filesystem — cx-studio 文件系统工具子包。

对外统一导出路径类型（Path / PathLike）、路径工具集（PathUtils）、
文件编码探测（detect_file_encoding）、文件列表与大小/信息缓存
（FileList / FileSizer / FileInfoCache）以及可执行文件查找与路径
展开工具（CmdFinder / PathExpander / SuffixFinder）。
"""

import os
import pathlib

Path = pathlib.Path
PathLike = os.PathLike

from . import path_utils as PathUtils
from .path_expander import *
from .encoding_detector import *
from .file_info_cache import FileInfoCache
from .file_sizer import *
from .file_list import *

__all__ = [
    "Path",
    "PathLike",
    "CmdFinder",
    "PathExpander",
    "SuffixFinder",
    "detect_file_encoding",
    "FileSizer",
    "FileList",
    "FileInfoCache",
    "PathUtils",
]
