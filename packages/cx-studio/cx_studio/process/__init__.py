"""子进程与流处理工具包。

``StreamUtils`` 为基于 ``subprocess``/``IO`` 的同步实现，
``AsyncStreamUtils`` 为基于 ``asyncio`` 的异步实现；两者提供同名 API
（``create_subprocess``/``wrap_io``/``read_stream`` 等），调用方按自身
同步/异步上下文选用对应模块。
"""

from . import stream_utils as StreamUtils
from . import stream_utils_async as AsyncStreamUtils
