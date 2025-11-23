from pathlib import Path


class FFmpegFilePathPreProcessor:
    """
    对FFmpeg命令行参数中的文件路径进行预处理
    """

    def __init__(self, *arguments) -> None:
        self._arguments = arguments
        self._inputs = []
        self._outputs = []
        self.process(*arguments)

    def process(self, *arguments) -> None:
        self._inputs.clear()
        self._outputs.clear()

        prev = ""
        for arg in arguments:
            arg = str(arg).strip()
            if not arg.startswith("-"):
                if prev == "-i":
                    self._inputs.append(arg)
            else:
                self._outputs.append(arg)
            prev = arg

    @property
    def inputs(self) -> list[str]:
        return self._inputs

    @property
    def outputs(self) -> list[str]:
        return self._outputs
