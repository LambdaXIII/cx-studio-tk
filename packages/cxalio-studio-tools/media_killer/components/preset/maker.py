"""MissionMaker 任务生成器。

基于 Preset 模板和源文件路径，通过标签替换和路径解析，
生成完全自洽的 Mission 值对象。
"""

from __future__ import annotations

from pathlib import Path

from ...media import InputSpec, Mission, OutputSpec
from .preset import Preset
from .tag_replacer import PresetTagReplacer


def _resolve_input_path(filename: Path, preset_dir: Path) -> Path:
    """解析输入文件路径为绝对路径。

    相对路径优先基于预设文件目录解析，若该路径不存在则回退到 CWD。

    Args:
        filename: 待解析的文件路径
        preset_dir: 预设文件所在目录

    Returns:
        Path: 解析后的绝对路径
    """
    if filename.is_absolute():
        return filename.resolve()

    preset_based = (preset_dir / filename).resolve()
    if preset_based.exists():
        return preset_based

    return (Path.cwd() / filename).resolve()


def _resolve_output_path(filename: Path, output_dir: Path) -> Path:
    """解析输出文件路径为绝对路径。

    相对路径基于输出目录解析。

    Args:
        filename: 待解析的文件路径
        output_dir: 输出目录

    Returns:
        Path: 解析后的绝对路径
    """
    if filename.is_absolute():
        return filename.resolve()

    return (output_dir / filename).resolve()


class MissionMaker:
    """Mission 任务生成器。

    接收 Preset，对每个源文件执行标签替换和路径解析，
    生成完全自洽的 Mission 值对象。
    """

    def __init__(self, preset: Preset) -> None:
        """初始化任务生成器。

        Args:
            preset: 预设对象
        """
        self._preset = preset

    def make_mission(
        self,
        source: Path,
        output_dir: Path | None = None,
        overwrite_mode: str | None = None,
    ) -> Mission:
        """生成 Mission。

        Args:
            source: 源文件路径
            output_dir: 输出目录。若为 None，使用 CWD。
            overwrite_mode: 覆盖模式三态。``None`` 沿用 preset 设置，
                ``"danger"`` 强制覆盖，``"safe"`` 禁止覆盖。

        Returns:
            Mission: 生成的 Mission 对象
        """
        resolved_output_dir = (output_dir or Path.cwd()).resolve()
        replacer = PresetTagReplacer(self._preset, source, resolved_output_dir)
        preset_dir = self._preset.path.parent

        # 替换全局 options
        options = replacer.read_value_as_list(self._preset.options)

        # 替换输入模板并解析路径
        inputs: list[InputSpec] = []
        for template in self._preset.inputs:
            raw_filename = Path(replacer.read_value(template.filename))
            filename = _resolve_input_path(raw_filename, preset_dir)
            opts = replacer.read_value_as_list(template.options)
            inputs.append(InputSpec(filename=filename, options=opts))

        # 替换输出模板并解析路径
        outputs: list[OutputSpec] = []
        for template in self._preset.outputs:
            raw_filename = Path(replacer.read_value(template.filename))
            filename = _resolve_output_path(raw_filename, resolved_output_dir)
            opts = replacer.read_value_as_list(template.options)
            outputs.append(OutputSpec(filename=filename, options=opts))

        # 覆盖逻辑：overwrite_mode 优先于 Preset 配置
        overwrite = self._preset.overwrite
        if overwrite_mode == "danger":
            overwrite = True
        elif overwrite_mode == "safe":
            overwrite = False

        return Mission(
            ffmpeg=self._preset.ffmpeg,
            source=source.resolve(),
            standard_target=replacer.standard_target,
            overwrite=overwrite,
            options=list(options),
            inputs=inputs,
            outputs=outputs,
            preset_id=self._preset.id,
            preset_name=self._preset.name,
        )
