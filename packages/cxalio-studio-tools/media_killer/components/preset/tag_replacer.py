"""PresetTagReplacer 标签替换器。

基于 Preset 配置，将模板字符串中的标签变量替换为实际值，
并计算标准目标文件路径。
"""

from __future__ import annotations

import os
from pathlib import Path

from cx_studio.filesystem import PathUtils
from cx_studio.text import PathInfoProvider, TagReplacer

from .preset import Preset


class PresetTagReplacer:
    """Preset 标签替换器。

    接收 Preset + source + output_dir，输出替换后的字符串。
    支持 ${source:*}、${target:*}、${preset:*}、${custom:*} 等标签变量。
    """

    def __init__(
        self,
        preset: Preset,
        source: Path,
        output_dir: Path | None = None,
    ) -> None:
        self._preset = preset
        self._source = Path(source).resolve()
        self._output_dir = (output_dir or Path.cwd()).resolve()

        # 第一步：构建不含 target 的 replacer
        self._replacer = self._build_replacer(with_target=False)

        # 第二步：计算目标路径（target_folder 通过 read_value 替换标签）
        self._target = self._compute_target()

        # 第三步：安装 target provider（路径已完全解析）
        self._replacer.install_provider("target", PathInfoProvider(self._target))

    def _compute_target(self) -> Path:
        """计算目标文件路径。

        Returns:
            Path: 完整的目标文件路径
        """
        # 1. 确定输出基础目录（target_folder 先经 read_value 替换标签）
        output_dir = self._output_dir
        target_folder_str = self.read_value(str(self._preset.target_folder))
        target_folder = Path(target_folder_str)
        if target_folder.is_absolute():
            output_dir = target_folder
        else:
            output_dir = Path(output_dir, target_folder)

        # 2. 获取父目录层级
        parent_dirs = PathUtils.get_parents(
            self._source, self._preset.keep_parent_level
        )

        # 3. 构造目标文件名
        target_name = PathUtils.force_suffix(
            PathUtils.get_basename(self._source), self._preset.target_suffix
        )

        # 4. 完整目标路径
        return Path(output_dir, *parent_dirs, target_name).resolve()

    def _build_replacer(self, with_target: bool = True) -> TagReplacer:
        """构建标签替换器并注册 providers。

        Args:
            with_target: 是否安装 target provider。首次构建时为 False，
                target 路径尚未解析完成；计算完毕后再手动安装。

        Returns:
            TagReplacer: 配置好的替换器实例
        """
        replacer = TagReplacer()

        # 注册 providers（target 依赖 _target，首次构建时跳过）
        replacer.install_provider("preset", self._provide_preset_info)
        replacer.install_provider("profile", self._provide_preset_info)  # 别名
        replacer.install_provider("custom", self._provide_custom_values)
        replacer.install_provider("source", PathInfoProvider(self._source))
        if with_target:
            replacer.install_provider("target", PathInfoProvider(self._target))
        replacer.install_provider("sep", os.sep)

        return replacer

    def _provide_preset_info(self, param: str) -> str | None:
        """提供预设信息。

        Args:
            param: 参数名（id/name/description/folder/folder_name/input_count/output_count）

        Returns:
            str | None: 对应的预设信息，未匹配返回 None
        """
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
        """提供自定义值。

        Args:
            param: 参数名（可带额外参数，取第一个单词）

        Returns:
            str | None: 对应的自定义值，未找到返回 None
        """
        param = str(param).split(" ")[0].lower()  # 取第一个单词，转小写
        result = self._preset.custom.get(param)
        return str(result) if result else None

    def read_value(self, value: str) -> str:
        """替换字符串中的标签变量。

        Args:
            value: 包含标签变量的字符串

        Returns:
            str: 替换后的字符串
        """
        return self._replacer.replace(value)

    def read_value_as_list(self, value: str | list) -> list[str]:
        """替换并拆分为列表。

        Args:
            value: 字符串或列表

        Returns:
            list[str]: 替换并拆分后的列表
        """
        if isinstance(value, list):
            # 递归处理列表中的每个元素
            result = []
            for item in value:
                if isinstance(item, str):
                    replaced = self.read_value(item)
                    result.extend(replaced.split())
                elif isinstance(item, list):
                    result.extend(self.read_value_as_list(item))
            return result
        else:
            # 字符串：先替换标签，再按空格拆分
            replaced = self.read_value(value)
            return replaced.split()

    @property
    def standard_target(self) -> Path:
        """返回标准目标文件路径（已完成标签替换和锚点解析）。

        Returns:
            Path: 标准目标文件路径
        """
        return self._target
