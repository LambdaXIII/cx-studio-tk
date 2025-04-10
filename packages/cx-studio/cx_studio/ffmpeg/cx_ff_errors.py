
from ctypes import ArgumentError


class FFmpegError:
    def __init__(self) -> None:
        self.message:str = ""
        self.output:str|None = None

class NoFFmpegExecutableError(ArgumentError,FFmpegError):
    def __init__(self, message: str = "No availuable ffmpeg excutable.",output:str|None=None) -> None:
        super().__init__()
        self.message = message
        self.output = output

class FFmpegIsRunningError(RuntimeError,FFmpegError):
    def __init__(self, message: str = "Same ffmpeg already excuted.",output:str|None=None) -> None:
        super().__init__()
        self.message = message
        self.output = output

        
