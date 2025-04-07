from .mission import Mission
from .preset import Preset


class MissionRunner:
    def __init__(self, mission: Mission) -> None:
        self._mission = mission

    @property
    def mission(self) -> Mission:
        return self._mission

    @property
    def preset(self) -> Preset:
        return self._mission.preset

    def run(self) -> None:
        pass
