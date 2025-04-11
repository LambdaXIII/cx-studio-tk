from cx_studio.utils import TextUtils
from collections.abc import Generator, Iterable


class EmptyFFmpeg:
    def __init__(self) -> None:
        self._executable = ""
        self._arguments: list[str] = []

    @property
    def executable(self) -> str:
        return self._executable

    @property
    def arguments(self) -> list[str]:
        return self._arguments

    def iter_arguments(
        self, include_executable: bool = False, auto_auote: bool = False
    ) -> Generator[str]:
        if include_executable:
            yield self.executable
        for argument in self._arguments:
            if argument.startswith("-"):
                yield argument
            else:
                yield TextUtils.auto_quote(argument) if auto_auote else argument

    def set_arguments(self, arguments: Iterable[str]):
        self._arguments[:] = list(arguments)
        return self

    def extend_arguments(self, arguments: Iterable[str]):
        self._arguments.extend(arguments)
        return self

    def add_arguments(self, *args):
        self._arguments.extend(args)

    def iter_argument_pairs(self) -> Generator[tuple[str | None, str | None]]:
        prev = None
        for argument in self.iter_arguments():
            if argument.startswith("-"):
                if prev:
                    yield prev, None
                prev = argument
            else:
                yield prev, argument
                if prev:
                    prev = None
