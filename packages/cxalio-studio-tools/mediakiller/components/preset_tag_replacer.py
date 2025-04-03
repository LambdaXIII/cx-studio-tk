from pathlib import Path

from cx_studio.tag_replacer import TagReplacer, PathInfoProvider
from cx_studio.utils import PathUtils
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

        output_dir = output_dir or Path.cwd()
        target_folder = self._preset.target_folder
        if target_folder.is_absolute():
            output_dir = target_folder
        else:
            output_dir = Path(output_dir, target_folder)
        parent_dirs = PathUtils.get_parents(source, self._preset.keep_parent_level)
        target_name = PathUtils.force_suffix(
            PathUtils.get_basename(source), self._preset.target_suffix
        )
        self._target = Path(output_dir, *parent_dirs, target_name).resolve()
        self.replacer.install_provider("target", PathInfoProvider(self._target))

    @property
    def standard_target(self):
        return self._target

    def _provide_preset_info(self, param: str):
        param = str(param).split(" ")[0].lower()
        match param:
            case "id":
                return self._preset.id
            case "name":
                return self._preset.name
            case "description":
                return self._preset.description
            case "folder":
                return self._preset.path.parent
            case "folder_name":
                return self._preset.path.parent.name
            case "input_count":
                return len(self._preset.inputs)
            case "output_count":
                return len(self._preset.outputs)
        return None

    def _provide_custom_values(self, param: str):
        param = str(param).split(" ")[0].lower()
        return self._preset.custom.get(param, None)

    def read_value(self, value: str) -> str:
        return self.replacer.replace(value)

    def read_value_as_list(self, value: str | list):
        if isinstance(value, list):
            for v in value:
                yield from self.read_value_as_list(v)
        else:
            value = str(value)
            if " " in value:
                yield from self.read_value_as_list(value.split(" "))
            else:
                yield self.read_value(value)
