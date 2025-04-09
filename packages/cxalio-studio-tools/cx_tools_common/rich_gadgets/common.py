from typing import Protocol, runtime_checkable
from collections.abc import Generator


@runtime_checkable
class RichPrettyMixin(Protocol):
    def __rich_repr__(self): ...
