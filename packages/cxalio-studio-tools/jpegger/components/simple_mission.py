from pathlib import Path
from ..filters import ImageFilterChain
from pydantic import BaseModel, Field
from cx_studio.utils import PathUtils


class Mission(BaseModel):
    source: Path
    target: Path
    filter_chain: ImageFilterChain = ImageFilterChain([])


class SimpleMissionBuilder:
    def __init__(self, filter_chain: ImageFilterChain, output_dir: Path | None):
        self.output_dir = PathUtils.normalize_path(output_dir or Path.cwd())
        self.filter_chain = filter_chain

    def make_mission(self, source: Path) -> Mission:
        source = PathUtils.normalize_path(source)
        target = PathUtils.take_dir(source) / source.name
        return Mission(source=source, target=target, filter_chain=self.filter_chain)
