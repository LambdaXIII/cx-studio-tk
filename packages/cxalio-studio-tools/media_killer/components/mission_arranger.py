from typing import Generator, Literal

from cx_tools_common.rich_gadgets.rich_label import RichLabel


from .mission import Mission
from operator import attrgetter

from media_killer.appenv import appenv


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

    def __no_sort(self) -> Generator[Mission]:
        yield from self.missions

    def __sort_by_source(self) -> Generator[Mission]:
        yield from sorted(self.missions, key=attrgetter("source"))

    def __sort_by_target(self) -> Generator[Mission]:
        yield from sorted(self.missions, key=attrgetter("standard_target"))

    def __sort_by_preset(self) -> Generator[Mission]:
        yield from sorted(self.missions, key=lambda x: x.preset.id)

    def __iter__(self) -> Generator[Mission]:
        cache = set()
        for m in self._sorters[self.sort_mode]():
            if m in cache:
                appenv.say(RichLabel(m), "是重复任务，已自动排除。")
                continue
            cache.add(m)
            yield m
