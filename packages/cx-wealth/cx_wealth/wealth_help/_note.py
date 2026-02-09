from typing import override

from ._node import _Node
from .. import rich_types as r


class _Note(_Node):
    def __init__(
        self,
        *contents: r.RenderableType,
        title: r.RenderableType | None = None,
        parent: _Node | None = None,
    ) -> None:
        super().__init__(title, None, parent)
        self.title = title
        self.contents = list(contents)

    @override
    def render_usage(self) -> r.Text:
        return r.Text()

    @override
    @r.group(True)
    def render_details(self):
        has_title = self.title is not None
        if has_title:
            yield self.title
        for content in self.contents:
            if has_title:
                yield r.Padding(content, pad=(0, 0, 0, 4))
            else:
                yield content

    def add_content(self, content: r.RenderableType) -> None:
        self.contents.append(content)
