from typing import overload, override

from cx_wealth._rich import Text
from ._node import _Node
from .. import _rich as r


class _RenderableNode(_Node):
    def __init__(self, *renderables: r.RenderableType):
        super().__init__()
        self.renderables = renderables

    @override
    def render_useage(self) -> Text:
        return r.Text()

    @overload
    @r.group(True)
    def render_details(self):
        yield from self.renderables
