
from codecs import StreamReader
from pyee import EventEmitter
from cx_studio.path_expander import CmdFinder
from pathlib import Path
from .cx_ff_infos import FFmpegCodingInfo
import threading
from collections.abc import Iterable,Generator
from cx_studio.utils import TextUtils
from .utils.empty_ffmpeg import EmptyFFmpeg
from typing import IO
from .cx_ff_errors import *
import io,os
import subprocess

class FFmpeg(EventEmitter,EmptyFFmpeg):
    def __init__(self, ffmpeg_executable: str | Path | None = None, arguments: Iterable[str] |None= None):
        super().__init__()
        self._executable:str = str(CmdFinder.which(ffmpeg_executable or "ffmpeg"))
        self._arguments = list(arguments or [])
        self._coding_info = FFmpegCodingInfo()
        self._is_running = False
        self._wanna_cancel = threading.Event()

    def cancel(self):
        self._wanna_cancel.set()

    @staticmethod
    def wrap_io(stream:IO[bytes]|bytes)->IO[bytes]:
        # if stream is None:
        #     return io.BytesIO(b"")
        if isinstance(stream,bytes):
            return io.BytesIO(stream)
        return stream
    @staticmethod
    def create_process(*args,**kwargs):
        # On Windows, CREATE_NEW_PROCESS_GROUP flag is required to use CTRL_BREAK_EVENT signal,
        # which is required to gracefully terminate the FFmpeg process.
        # Reference: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.send_signal
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore

        return subprocess.Popen(*args, **kwargs)

    def _record_stdout(self):
        pass

    def _handle_stderr(self,stream):
        pass

    def _write_stdin(self,stream:bytes|IO[bytes]|None = None):
        pass

    def terminate(self):
        pass

    def kill(self):
        pass

    def execute(self,input_stream:bytes|IO[bytes]|None = None):
        if self._is_running:
            raise FFmpegIsRunningError("FFmpeg is already running.")
        
        if input_stream:
            input_stream = self.wrap_io(input_stream)
        
        self._wanna_cancel.clear()
        self._is_running = True

        self._process = self.create_process(
            list(self.iter_arguments(True))
            bufsize=0,
            stdin=subprocess.PIPE if (stream is not None) else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.emit("started")






    


    
