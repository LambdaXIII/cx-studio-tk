import os
from collections.abc import Generator
from pathlib import Path

from cx_studio.text import TagReplacer, PathInfoProvider
from cx_studio.filesystem import *
from .preset import Preset


class PresetTagReplacer:
    def __init__(self, preset: Preset, source: Path, output_dir: Path | None = None):
        self._preset = preset
        self._source = Path(source)
        self.replacer = TagReplacer()
        self.replacer.install_provider("preset", self._provide_preset_info)
        self.replacer.install_provider("profile", self._provide_preset_info)
        self.replacer.install_provider("custom", self._provide_custom_values)
        self.replacer.install_provider("source", PathInfoProvider(self._source))
        self.replacer.install_provider("sep", os.sep)

        output_dir = (output_dir or Path.cwd()).resolve()
        target_folder = Path(self._preset.target_folder)
        if target_folder.is_absolute():
            output_dir = target_folder
        else:
            output_dir = Path(output_dir, target_folder)
        parent_dirs = PathUtils.get_parents(source, self._preset.keep_parent_level)
        target_name = PathUtils.force_suffix(
            PathUtils.get_basename(source), self._preset.target_suffix
        )
        self._target = Path(output_dir, *parent_dirs, target_name).resolve()
        self.replacer.install_provider("target", PathInfoProvider(self.standard_target))

    @property
    def standard_target(self) -> Path:
        return Path(self.read_value(str(self._target)))

    def _provide_preset_info(self, param: str) -> str | None:
        param = str(param).lower()
        match param:
            case "id":
                return self._preset.id
            case "name":
                return self._preset.name
            case "description":
                return self._preset.description
            case "folder":
                return str(self._preset.path.parent)
            case "folder_name":
                return self._preset.path.parent.name
            case "input_count":
                return str(len(self._preset.inputs))
            case "output_count":
                return str(len(self._preset.outputs))
        return None

    def _provide_custom_values(self, param: str) -> str | None:
        param = str(param).split(" ")[0].lower()
        result = self._preset.custom.get(param)
        return str(result) if result else None

    def read_value(self, value: str) -> str:
        return self.replacer.replace(value)

    def read_value_as_list(self, value: str | list) -> Generator[str]:
        if isinstance(value, list):
            for v in value:
                yield from self.read_value_as_list(v)
        else:
            value = self.read_value(value)
            if " " in value:
                yield from self.read_value_as_list(value.split(" "))
            else:
                yield self.read_value(value)
