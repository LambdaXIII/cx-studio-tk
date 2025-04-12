import io
import re
import subprocess
import sys
from datetime import timedelta
from typing import IO, Any
from collections.abc import AsyncIterable, Awaitable, Iterable
import asyncio



def create_subprocess(*args: Any, **kwargs: Any) -> Awaitable[asyncio.subprocess.Process]:
    # On Windows, CREATE_NEW_PROCESS_GROUP flag is required to use CTRL_BREAK_EVENT signal,
    # which is required to gracefully terminate the FFmpeg process.
    # Reference: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.send_signal
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore

    return asyncio.create_subprocess_exec(*args, **kwargs)


def wrap_io(stream: bytes | asyncio.StreamReader | None) -> asyncio.StreamReader:
    if isinstance(stream, asyncio.StreamReader):
        return stream
    
    reader = asyncio.StreamReader()
    reader.feed_data(stream or b"")
    reader.feed_eof()
    return reader


async def read_stream(stream: asyncio.StreamReader, size: int = -1) -> AsyncIterable[bytes]:
    while not stream.at_eof():
        chunk = await stream.read(size)
        if not chunk:
            break
        yield chunk


async def readlines_from_stream(stream: asyncio.StreamReader) -> AsyncIterable[bytes]:
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
    if stream is None:
        return b""

    buffer = bytearray()
    async for chunk in read_stream(stream, io.DEFAULT_BUFFER_SIZE):
        buffer.extend(chunk)

    # stream.close()
    return bytes(buffer)


async def redirect_stream(stream_from: asyncio.StreamReader | None, stream_to: asyncio.StreamWriter | None):
    if stream_from is None or stream_to is None:
        return
    assert stream_from is not None
    assert stream_to is not None

    async for chunk in read_stream(stream_from, io.DEFAULT_BUFFER_SIZE):
        stream_to.write(chunk)
        await stream_to.drain()

    
