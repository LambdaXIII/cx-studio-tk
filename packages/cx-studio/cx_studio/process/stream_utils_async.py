"""子进程与二进制流的异步（asyncio）处理工具。

提供跨平台子进程创建（Windows 下自动附加 ``CREATE_NEW_PROCESS_GROUP``
标志，以支持用 ``CTRL_BREAK_EVENT`` 优雅终止 FFmpeg 进程），以及基于
``asyncio.StreamReader``/``asyncio.StreamWriter`` 的流读取、按行切分、
整流收集与转发等辅助函数。

与 ``cx_studio.process.stream_utils`` 同步版本功能对应；本模块的函数
均为协程或异步生成器，须在事件循环中 ``await``（或以 ``async for`` 消费）。
"""

import asyncio
import io
import re
import subprocess
import sys
from collections.abc import AsyncIterable, Awaitable
from typing import Any


def create_subprocess(
    *args: Any, **kwargs: Any
) -> Awaitable[asyncio.subprocess.Process]:
    """创建子进程（``asyncio.create_subprocess_exec`` 的薄封装）。

    返回可等待对象，须在事件循环中 ``await`` 后得到已启动的进程。
    在 Windows 上自动附加 ``CREATE_NEW_PROCESS_GROUP`` creationflag，
    以便之后可用 ``CTRL_BREAK_EVENT`` 信号优雅终止进程。

    Args:
        *args: 传给 ``asyncio.create_subprocess_exec`` 的程序路径与位置参数。
        **kwargs: 传给 ``asyncio.create_subprocess_exec`` 的关键字参数
            （Windows 下 ``creationflags`` 会被本函数覆盖为注入的值）。

    Returns:
        await 后得到 ``asyncio.subprocess.Process`` 的可等待对象。
    """
    # On Windows, CREATE_NEW_PROCESS_GROUP flag is required to use CTRL_BREAK_EVENT signal,
    # which is required to gracefully terminate the FFmpeg process.
    # Reference: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.send_signal
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore

    return asyncio.create_subprocess_exec(*args, **kwargs)


def wrap_io(stream: bytes | asyncio.StreamReader | None) -> asyncio.StreamReader:
    """将输入统一包装为 ``asyncio.StreamReader``。

    包装规则：
    - 已是 ``StreamReader`` → 原样返回；
    - ``bytes`` 或 ``None`` → 新建 ``StreamReader``，将字节串内容喂入
      （``None`` 视为 ``b""``）并立即置 EOF，使读取方读到数据后即正常结束。

    Args:
        stream: 待包装的 ``StreamReader``、字节串或 ``None``。

    Returns:
        可异步读取的 ``asyncio.StreamReader``。
    """
    if isinstance(stream, asyncio.StreamReader):
        return stream

    reader = asyncio.StreamReader()
    reader.feed_data(stream or b"")
    reader.feed_eof()
    return reader


async def read_stream(
    stream: asyncio.StreamReader, size: int = -1
) -> AsyncIterable[bytes]:
    """异步按块读取流并逐个产出（异步生成器）。

    每次 ``await read(size)`` 读取一块，直到流到达 EOF
    （``at_eof()``）或读到空块。须用 ``async for`` 消费。

    Args:
        stream: 待读取的 ``asyncio.StreamReader``。
        size: 每次读取的字节数，默认 -1（一次读尽剩余内容）。

    Yields:
        依次产出的字节块；流为空时无产出。
    """
    while not stream.at_eof():
        chunk = await stream.read(size)
        if not chunk:
            break
        yield chunk


async def readlines_from_stream(stream: asyncio.StreamReader) -> AsyncIterable[bytes]:
    """从流中异步按行读取并产出（不含行尾分隔符，异步生成器）。

    以 ``\\r``、``\\n`` 及其任意连续组合作为行分隔符：连续分隔符之间
    会产出空行，与 ``bytes.splitlines`` 的空白行处理一致。内部按块
    累积缓冲并切分；流结束时的残余内容（末尾不带换行）也作为一行产出。

    Args:
        stream: 待读取的 ``asyncio.StreamReader``。

    Yields:
        不含行尾分隔符的字节行，最后可能包含无换行结尾的残余内容。
    """
    pattern = re.compile(rb"[\r\n]+")

    buffer = bytearray()
    async for chunk in read_stream(stream, io.DEFAULT_BUFFER_SIZE):
        buffer.extend(chunk)

        lines = pattern.split(buffer)
        buffer[:] = lines.pop(-1)  # keep the last line that could be partial

        for x in lines:
            yield x

    if buffer:
        yield bytes(buffer)


async def record_stream(stream: asyncio.StreamReader | None) -> bytes:
    """异步读取整个流并返回其全部内容（协程）。

    分块读取直到流结束，适合管道等无法预知长度或不宜整块读入的流。
    不关闭流。

    Args:
        stream: 待读取的 ``asyncio.StreamReader``，或 ``None``。

    Returns:
        流中的全部字节；``stream`` 为 ``None`` 时返回 ``b""``。
    """
    if stream is None:
        return b""

    buffer = bytearray()
    async for chunk in read_stream(stream, io.DEFAULT_BUFFER_SIZE):
        buffer.extend(chunk)

    # stream.close()
    return bytes(buffer)


async def redirect_stream(
    stream_from: asyncio.StreamReader | None, stream_to: asyncio.StreamWriter | None
):
    """异步将源流内容完整写入目标流（协程）。

    分块读取源流并 ``write`` 到目标流，每块后 ``await drain()`` 以
    背压控制，直到源流结束。不关闭任一流；任一参数为 ``None`` 时
    直接返回（不执行任何操作）。

    Args:
        stream_from: 源 ``asyncio.StreamReader``，或 ``None``。
        stream_to: 目标 ``asyncio.StreamWriter``，或 ``None``。
    """
    if stream_from is None or stream_to is None:
        return

    async for chunk in read_stream(stream_from, io.DEFAULT_BUFFER_SIZE):
        stream_to.write(chunk)
        await stream_to.drain()
