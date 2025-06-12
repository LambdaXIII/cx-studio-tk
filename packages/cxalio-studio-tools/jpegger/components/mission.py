from dataclasses import dataclass
from multiprocessing.pool import ThreadPool
from pathlib import Path

from cx_wealth.wealth_label import WealthLabel
from ..filters import ImageFilterChain
from pydantic import BaseModel, Field, ConfigDict
import ulid


class Mission(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    mission_id: ulid.ULID = Field(default_factory=ulid.new, kw_only=True)

    source: Path
    target: Path
    target_format: str | None
    filter_chain: ImageFilterChain = ImageFilterChain([])
    saving_options: dict = {}

    def __rich_label__(self):
        yield f"[yellow][>{self.target_format or "auto"}][/]"
        yield self.source.name
        yield f"[blue]=={len(self.filter_chain)}=>[/]"
        yield self.target.name
