from operator import attrgetter
from typing import Literal
from collections.abc import Generator

from cx_wealth.wealth_label import WealthLabel
from media_killer.appenv import appenv
from .mission import Mission


class MissionArranger:
    def __init__(
        self,
        missions: list[Mission],
        sort_mode: Literal["source", "target", "preset", "x"] = "x",
    ):
        self.missions = missions
        self.sort_mode = sort_mode

        self._sorters = {
            "source": self.__sort_by_source,
            "target": self.__sort_by_target,
            "preset": self.__sort_by_preset,
            "x": self.__no_sort,
        }

    def __no_sort(self) -> Generator[Mission, None, None]:
        yield from self.missions

    def __sort_by_source(self) -> Generator[Mission, None, None]:
        yield from sorted(self.missions, key=attrgetter("source"))

    def __sort_by_target(self) -> Generator[Mission, None, None]:
        yield from sorted(self.missions, key=attrgetter("standard_target"))

    def __sort_by_preset(self) -> Generator[Mission, None, None]:
        yield from sorted(self.missions, key=lambda x: x.preset_id)

    def __iter__(self) -> Generator[Mission, None, None]:
        cache = set()
        for m in self._sorters[self.sort_mode]():
            if m in cache:
                appenv.say(WealthLabel(m), "是重复任务，已自动排除。")
                continue
            cache.add(m)
            yield m
