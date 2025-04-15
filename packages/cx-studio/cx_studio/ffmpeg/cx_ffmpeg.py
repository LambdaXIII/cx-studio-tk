
from copy import copy
from pyee import EventEmitter
from cx_studio.path_expander import CmdFinder
from pathlib import Path
from .cx_ff_infos import FFmpegCodingInfo
import threading
from collections.abc import Iterable, Generator
from cx_studio.utils import TextUtils, StreamUtils
from .utils.basic_ffmpeg import BasicFFmpeg
from typing import IO
from .cx_ff_errors import *
import io, os
import subprocess
import concurrent.futures as con_futures
import sys, signal

import dataclasses
class FFmpeg(EventEmitter, BasicFFmpeg):
    def __init__(
        self,
        ffmpeg_executable: str | Path | None = None,
        arguments: Iterable[str] | None = None,
    ):
        super().__init__()
        self._executable: str = str(CmdFinder.which(ffmpeg_executable or "ffmpeg"))
        self._arguments = list(arguments or [])
        self._coding_info = FFmpegCodingInfo()
        self._is_running = False
        self._canceled: bool = False

        self._process: subprocess.Popen[bytes]

    def is_running(self) -> bool:
        return self._is_running

    def cancel(self):
        if not self._is_running or not self._process:
            return
        sigterm = signal.SIGTERM if sys.platform != "win32" else signal.CTRL_BREAK_EVENT
        self._canceled = True
        self._process.send_signal(sigterm)

    @property
    def coding_info(self):
        return self._coding_info

    def _handle_stderr(self):
        assert self._process.stderr is not None
        line = b""
        for line in StreamUtils.readlines_from_stream(self._process.stderr):
            decoded = line.decode()
            self._coding_info.update_from_status_line(decoded)
            self.emit("coding_info_updated", copy(self._coding_info))
            self.emit("verbose",decoded)
            if 'frame' in decoded:
                self.emit(
                    "progress_updated",
                    self._coding_info.current_time,
                    self._coding_info.total_time,
                )
        return line.decode()

    def execute(
        self,
        input_stream: bytes | IO[bytes] | None = None,
        timeout: float | None = None,
    ):
        """
        Args:
            stream: A stream to input to the standard input. Defaults to None.
            timeout: The maximum number of seconds to wait before returning. Defaults to None.

        Raises:
            FFmpegAlreadyExecuted: If FFmpeg is already executed.
            FFmpegError: If FFmpeg process returns non-zero exit status.
            subprocess.TimeoutExpired: If FFmpeg process does not terminate after `timeout` seconds.
        """
        args = list(self.iter_arguments(True))

        if self._is_running:
            raise FFmpegIsRunningError("FFmpeg is already running.", args)

        input_stream = StreamUtils.wrap_io(input_stream)

        self._process = StreamUtils.create_subprocess(
            args,
            bufsize=0,
            stdin=subprocess.PIPE if (input_stream is not None) else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        with con_futures.ThreadPoolExecutor(max_workers=4) as pool:
            self._is_running = True
            self.emit("started", args)
            futures = [
                pool.submit(
                    StreamUtils.redirect_stream, input_stream, self._process.stdin
                ),
                pool.submit(StreamUtils.record_stream, self._process.stdout),
                pool.submit(self._handle_stderr),
                pool.submit(self._process.wait, timeout),
            ]
            done, pending = con_futures.wait(
                futures, return_when=con_futures.FIRST_EXCEPTION
            )
            self._is_running = False

            for f in done:
                exc = f.exception()
                if exc is not None:
                    self._process.terminate()
                    con_futures.wait(pending)
                    return exc

            if self._process.returncode == 0:
                self.emit("finished")
            elif self._canceled:
                self.emit("canceled")
            else:
                raise FFmpegError.create(message=futures[2].result(), arguments=args)
            return futures[1].result()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._process is not None:
            self._process.terminate()
            self._process.wait()
