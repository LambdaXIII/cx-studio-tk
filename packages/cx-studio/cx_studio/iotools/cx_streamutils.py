import io
import re
import subprocess
import sys
from typing import IO, Any, Iterable


def create_subprocess(*args: Any, **kwargs: Any) -> subprocess.Popen:
    # On Windows, CREATE_NEW_PROCESS_GROUP flag is required to use CTRL_BREAK_EVENT signal,
    # which is required to gracefully terminate the FFmpeg process.
    # Reference: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.send_signal
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore

    return subprocess.Popen(*args, **kwargs)


def wrap_io(stream: bytes | IO[bytes] | None) -> IO[bytes]:
    if stream is None:
        return io.BytesIO(b"")
    if isinstance(stream, bytes):
        stream = io.BytesIO(stream)
    return stream


def read_stream(stream: IO[bytes], size: int = -1) -> Iterable[bytes]:
    while True:
        chunk = stream.read(size)
        if not chunk:
            break

        yield chunk


def readlines_from_stream(stream: IO[bytes]) -> Iterable[bytes]:
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
    if stream is None:
        return b""

    buffer = bytearray()
    for chunk in read_stream(stream, io.DEFAULT_BUFFER_SIZE):
        buffer.extend(chunk)

    # stream.close()
    return bytes(buffer)


def redirect_stream(stream_from: IO[bytes] | None, stream_to: IO[bytes] | None):
    if stream_from is None or stream_to is None:
        return
    for chunk in read_stream(stream_from, io.DEFAULT_BUFFER_SIZE):
        stream_to.write(chunk)
    stream_to.flush()
    # stream_to.close()
