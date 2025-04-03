from pathlib import Path

from .argument_group import ArgumentGroup
from .mission import Mission
from .preset import Preset
from .preset_tag_replacer import PresetTagReplacer


class MissionMaker:
    def __init__(self, preset: Preset):
        self._preset = preset

    def make_mission(self, source: Path) -> Mission:
        replacer = PresetTagReplacer(self._preset, source)

        general = ArgumentGroup()
        general.add_options(replacer.read_value_as_list(self._preset.options))

        inputs = []
        for g in self._preset.inputs:
            x = ArgumentGroup()
            x.filename = Path(replacer.read_value(g.filename))
            x.add_options(replacer.read_value_as_list(g.options))
            inputs.append(x)

        outputs = []
        for g in self._preset.outputs:
            x = ArgumentGroup()
            x.filename = Path(replacer.read_value(g.filename))
            x.add_options(replacer.read_value_as_list(g.options))
            outputs.append(x)

        return Mission(
            preset=self._preset,
            source=source,
            standard_target=replacer.standard_target,
            overwrite=self._preset.overwrite,
            hardware_accelerate=self._preset.hardware_accelerate or "auto",
            options=general,
            inputs=inputs,
            outputs=outputs,
        )
