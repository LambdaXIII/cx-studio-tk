from typing import Protocol, runtime_checkable


@runtime_checkable
class RichPrettyMixin(Protocol):
    def __rich_repr__(self): ...
