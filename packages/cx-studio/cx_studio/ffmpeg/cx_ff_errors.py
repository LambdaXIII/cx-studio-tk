import re
from typing import ClassVar, Self


class FFmpegError(Exception):
    _patterns: ClassVar[list[str] | None] = None

    def __init__(self, message: str, arguments: list[str], output: str | None = None):
        super().__init__(message)
        self.message = message
        self.arguments = arguments
        self.output = output

    @classmethod
    def create(cls, message, arguments: list[str]) -> Self:
        """通过指定 _patterns 自动创建子类对象"""
        for subclass in cls.__subclasses__():
            if subclass._patterns is None:
                continue
            for pattern in subclass._patterns:
                if re.search(pattern, message, flags=re.IGNORECASE) is not None:
                    return subclass(message, arguments)
        return cls(message, arguments)


class FFmpegFileNotFoundError(FFmpegError):
    _patterns = [r"No such file", r"could not open"]


class FFmpegInvalidArgumentsError(FFmpegError):
    _patterns = [
        r"option .* ?not found",
        r"unrecognized option",
        r"trailing options were found on the commandline",
        r"invalid encoder type",
        r"codec not currently supported in container",
    ]


class FFmpegUnsupportedCodec(FFmpegError):
    _patterns = [
        r"unknown encoder",
        r"encoder not found",
        r"unknown decoder",
        r"decoder not found",
    ]


class FFmpegNoExecutableError(FFmpegError):
    pass


class FFmpegIsRunningError(FFmpegError):
    pass


# class FFmpegCanceledError(FFmpegError):
#     pass
