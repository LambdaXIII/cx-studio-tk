"""子进程与二进制流的同步处理工具。

提供跨平台子进程创建（Windows 下自动附加 ``CREATE_NEW_PROCESS_GROUP``
标志，以支持用 ``CTRL_BREAK_EVENT`` 优雅终止 FFmpeg 进程），以及基于
``IO[bytes]`` 的流读取、按行切分、整流收集与转发等辅助函数。
供同步调用方（如 FFmpeg 封装）使用；asyncio 版本见
``cx_studio.process.stream_utils_async``。
"""

import io
import re
import subprocess
import sys
from typing import IO, Any, Iterable


def create_subprocess(*args: Any, **kwargs: Any) -> subprocess.Popen:
    """创建子进程（``subprocess.Popen`` 的薄封装）。

    在 Windows 上自动附加 ``CREATE_NEW_PROCESS_GROUP`` creationflag，
    以便之后可用 ``CTRL_BREAK_EVENT`` 信号优雅终止进程。

    Args:
        *args: 传给 ``subprocess.Popen`` 的位置参数。
        **kwargs: 传给 ``subprocess.Popen`` 的关键字参数（Windows 下
            ``creationflags`` 会被本函数覆盖为注入的值）。

    Returns:
        已启动的 ``subprocess.Popen`` 对象。
    """
    # On Windows, CREATE_NEW_PROCESS_GROUP flag is required to use CTRL_BREAK_EVENT signal,
    # which is required to gracefully terminate the FFmpeg process.
    # Reference: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.send_signal
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore

    return subprocess.Popen(*args, **kwargs)


def wrap_io(stream: bytes | IO[bytes] | None) -> IO[bytes]:
    """将输入统一包装为可读的二进制流。

    包装规则：
    - ``None`` → 内容为空的 ``io.BytesIO``；
    - ``bytes`` → 以该字节串为内容的 ``io.BytesIO``；
    - 已是 ``IO[bytes]`` → 原样返回。

    Args:
        stream: 待包装的字节串、流对象或 ``None``。

    Returns:
        始终可读的二进制流（新构造的 ``io.BytesIO`` 或原流对象）。
    """
    if stream is None:
        return io.BytesIO(b"")
    if isinstance(stream, bytes):
        stream = io.BytesIO(stream)
    return stream


def read_stream(stream: IO[bytes], size: int = -1) -> Iterable[bytes]:
    """按块读取二进制流并逐个产出。

    每次调用 ``read(size)`` 读取一块，读到空块（流结束）即停止。
    分块读取适合管道等无法预知长度或不宜一次性读入内存的流。

    Args:
        stream: 待读取的二进制流。
        size: 每次读取的字节数，默认 -1（一次读尽剩余内容）。

    Yields:
        依次产出的字节块；流为空时无产出。
    """
    while True:
        chunk = stream.read(size)
        if not chunk:
            break

        yield chunk


def readlines_from_stream(stream: IO[bytes]) -> Iterable[bytes]:
    """从二进制流中按行读取并产出（不含行尾分隔符）。

    以 ``\\r``、``\\n`` 及其任意连续组合作为行分隔符：连续分隔符之间
    会产出空行，与 ``bytes.splitlines`` 的空白行处理一致。内部按块
    累积缓冲并切分；流结束时的残余内容（末尾不带换行）也作为一行产出。

    Args:
        stream: 待读取的二进制流。

    Yields:
        不含行尾分隔符的字节行，最后可能包含无换行结尾的残余内容。
    """
    pattern = re.compile(rb"[\r\n]+")

    buffer = bytearray()
    for chunk in read_stream(stream, io.DEFAULT_BUFFER_SIZE):
        buffer.extend(chunk)

        lines = pattern.split(buffer)
        buffer[:] = lines.pop(-1)  # keep the last line that could be partial

        yield from lines

    if buffer:
        yield bytes(buffer)


def record_stream(stream: IO[bytes] | None) -> bytes:
    """读取整个二进制流并返回其全部内容。

    与一次性 ``read()`` 等价，但采用分块读取，兼容管道等无法预知
    长度或不宜整块读入的流。不关闭流。

    Args:
        stream: 待读取的二进制流，或 ``None``。

    Returns:
        流中的全部字节；``stream`` 为 ``None`` 时返回 ``b""``。
    """
    if stream is None:
        return b""

    buffer = bytearray()
    for chunk in read_stream(stream, io.DEFAULT_BUFFER_SIZE):
        buffer.extend(chunk)

    # stream.close()
    return bytes(buffer)


def redirect_stream(stream_from: IO[bytes] | None, stream_to: IO[bytes] | None):
    """将源流内容完整复制到目标流并刷新。

    分块读取源流并写入目标流，直到源流结束，随后调用 ``flush()``。
    不关闭任一流；任一参数为 ``None`` 时直接返回（不执行任何操作）。

    Args:
        stream_from: 源二进制流，或 ``None``。
        stream_to: 目标二进制流，或 ``None``。
    """
    if stream_from is None or stream_to is None:
        return
    for chunk in read_stream(stream_from, io.DEFAULT_BUFFER_SIZE):
        stream_to.write(chunk)
    stream_to.flush()
    # stream_to.close()
