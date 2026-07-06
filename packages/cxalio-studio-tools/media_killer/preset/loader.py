"""Preset 文件加载器。

读取 TOML 预设文件，执行结构 lint 与标签 lint，构造 Preset 对象。
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

from cx_tools.i18n import _

from .preset import InputTemplate, OutputTemplate, Preset

# 有效的标签命名空间
_VALID_NAMESPACES: frozenset[str] = frozenset(
    {"source", "target", "preset", "profile", "custom", "sep"}
)

# 标签正则：${namespace:param}
_TAG_RE: re.Pattern[str] = re.compile(r"\$\{([^}]+)\}")

# 顶层必需节
_REQUIRED_SECTIONS: tuple[str, ...] = ("general", "source", "target", "input", "output")

# general 节必需字段
_REQUIRED_GENERAL: tuple[str, ...] = ("id", "name")


class PresetLoader:
    """TOML 预设文件加载器。

    负责读取 TOML、结构 lint、标签 lint、构造 Preset。
    不直接暴露 ``tomllib``，所有解析细节封装在内部。
    """

    def load(self, path: Path) -> Preset:
        """加载预设文件。

        Args:
            path: TOML 预设文件路径

        Returns:
            Preset: 加载的预设对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 预设文件格式错误或标签错误
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(_("预设文件不存在：{path}").format(path=path))

        data = self._read_toml(path)
        self._lint_structure(data, path)
        self._lint_tags(data, path)
        return self._build_preset(data, path)

    # ------------------------------------------------------------------
    # 内部步骤
    # ------------------------------------------------------------------

    @staticmethod
    def _read_toml(path: Path) -> dict[str, Any]:
        """读取并解析 TOML 文件。"""
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(
                _("TOML 解析失败（{path}）：{error}").format(path=path, error=e)
            ) from e

    @staticmethod
    def _lint_structure(data: dict[str, Any], path: Path) -> None:
        """检查 TOML 数据的结构完整性。

        验证必需顶层节和必需字段是否存在。
        """
        # 检查必需顶层节
        for section in _REQUIRED_SECTIONS:
            if section not in data:
                raise ValueError(
                    _("预设文件缺少必需节 [{section}]（{path}）").format(
                        section=section, path=path
                    )
                )

        # 检查 general 必需字段
        general = data["general"]
        for field_name in _REQUIRED_GENERAL:
            if field_name not in general:
                raise ValueError(
                    _('预设节 [general] 缺少必需字段 "{field}"（{path}）').format(
                        field=field_name, path=path
                    )
                )

        # 检查 input/output 为列表
        for section in ("input", "output"):
            if not isinstance(data[section], list):
                raise ValueError(
                    _("预设节 [{section}] 必须是列表（{path}）").format(
                        section=section, path=path
                    )
                )
            for i, item in enumerate(data[section]):
                if not isinstance(item, dict):
                    raise ValueError(
                        _(
                            "预设节 [{section}] 第 {index} 项必须是表格（{path}）"
                        ).format(section=section, index=i + 1, path=path)
                    )
                for field_name in ("filename", "options"):
                    if field_name not in item:
                        raise ValueError(
                            _(
                                "预设节 [{section}] 第 {index} 项缺少必需字段 "
                                '"{field}"（{path}）'
                            ).format(
                                section=section,
                                index=i + 1,
                                field=field_name,
                                path=path,
                            )
                        )

    @staticmethod
    def _lint_tags(data: dict[str, Any], path: Path) -> None:
        """检查 input/output 模板中的标签变量是否合法。

        仅验证标签格式和命名空间，不做实际值替换。
        """
        for section in ("input", "output"):
            for i, item in enumerate(data[section]):
                filename: str = item["filename"]
                for match in _TAG_RE.finditer(filename):
                    tag_body = match.group(1)
                    if ":" not in tag_body:
                        raise ValueError(
                            _(
                                "预设节 [{section}] 第 {index} 项的 filename "
                                '包含无效标签 "${{{tag}}}"：缺少命名空间分隔符 '
                                '"（{path}）'
                            ).format(
                                section=section,
                                index=i + 1,
                                tag=tag_body,
                                path=path,
                            )
                        )
                    namespace = tag_body.split(":", 1)[0]
                    if namespace not in _VALID_NAMESPACES:
                        raise ValueError(
                            _(
                                "预设节 [{section}] 第 {index} 项的 filename "
                                '包含未知标签命名空间 "${{{tag}}}"：'
                                "有效命名空间为 {valid}（{path}）"
                            ).format(
                                section=section,
                                index=i + 1,
                                tag=tag_body,
                                valid=", ".join(sorted(_VALID_NAMESPACES)),
                                path=path,
                            )
                        )

    @staticmethod
    def _build_preset(data: dict[str, Any], path: Path) -> Preset:
        """从已 lint 的 TOML 数据构造 Preset 对象。"""
        general = data["general"]
        source = data["source"]
        target = data["target"]

        return Preset(
            id=general["id"],
            name=general["name"],
            description=general.get("description", ""),
            path=path.resolve(),
            ffmpeg=general.get("ffmpeg", "ffmpeg"),
            overwrite=general.get("overwrite", False),
            hardware_accelerate=general.get("hardware_accelerate", "auto"),
            options=general.get("options", ""),
            source_suffixes=Preset.compute_source_suffixes(
                ignore_default=source.get("ignore_default_suffixes", False),
                includes=source.get("suffix_includes", []),
                excludes=source.get("suffix_excludes", []),
            ),
            target_suffix=target.get("suffix", ""),
            target_folder=Path(target.get("folder", ".")),
            keep_parent_level=target.get("keep_parent_level", 0),
            inputs=[InputTemplate(**inp) for inp in data["input"]],
            outputs=[OutputTemplate(**out) for out in data["output"]],
            custom=data.get("custom", {}),
        )
