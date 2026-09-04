"""FFmpeg 封装子包。

提供 FFmpeg 命令行参数预处理器（``FFmpegArgumentsPreProcessor``）、
媒体/进程/编码信息数据类（``FFmpegFormatInfo``/``FFmpegProcessInfo``/
``FFmpegCodingInfo``）与异步执行器（``FFmpegAsync``），并重导出其公开符号。
"""

from .ff_filepath_preprocessor import *
from .ff_infos import *
from .ffmpeg_async import *
