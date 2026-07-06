"""Mission 列表 XML 持久化存储。

MissionStore 负责将 Mission 列表序列化/反序列化为 XML 文件，
保持与旧版 last_missions.xml 的格式兼容。
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path

import ulid

from cx_studio.filesystem import ensure_parents
from ..mission import InputSpec, Mission, OutputSpec


def _text(element: ET.Element | None) -> str | None:
    """安全提取元素文本，元素为 None 时返回 None。"""
    if element is None:
        return None
    return element.text


def _parse_options(text: str | None) -> list[str]:
    """将空格分隔的选项字符串拆分为列表，空文本返回空列表。"""
    if not text or not text.strip():
        return []
    return text.strip().split()


class MissionStore:
    """Mission 列表的 XML 持久化存储。

    使用 ``xml.etree.ElementTree`` 将 Mission 列表序列化为 XML 文件，
    或从 XML 文件反序列化为 Mission 对象列表。
    """

    def save(self, path: Path, missions: Iterable[Mission]) -> None:
        """保存 Mission 列表到 XML 文件。

        Args:
            path: XML 文件路径
            missions: Mission 列表
        """
        root = ET.Element("missions")
        root.set("version", "1")

        for mission in missions:
            root.append(self._encode_mission(mission))

        tree = ET.ElementTree(root)
        path = ensure_parents(path)
        tree.write(path, encoding="utf-8", xml_declaration=True)

    def load(self, path: Path) -> list[Mission]:
        """从 XML 文件加载 Mission 列表。

        Args:
            path: XML 文件路径

        Returns:
            list[Mission]: Mission 列表，文件不存在时返回空列表
        """
        if not path.exists():
            return []

        tree = ET.parse(path)
        root = tree.getroot()

        return [self._decode_mission(node) for node in root.findall("mission")]

    @staticmethod
    def _encode_mission(mission: Mission) -> ET.Element:
        """将单个 Mission 序列化为 XML 元素。"""
        node = ET.Element("mission")

        _add_child(node, "mission_id", str(mission.mission_id))
        _add_child(node, "preset_id", mission.preset_id or "")
        _add_child(node, "preset_name", mission.preset_name or "")
        _add_child(node, "ffmpeg", mission.ffmpeg)
        _add_child(node, "source", str(mission.source))
        _add_child(node, "standard_target", str(mission.standard_target))
        _add_child(node, "overwrite", "true" if mission.overwrite else "false")
        _add_child(node, "hardware_accelerate", mission.hardware_accelerate or "")
        _add_child(node, "options", " ".join(mission.options))

        inputs_node = ET.SubElement(node, "inputs")
        for spec in mission.inputs:
            input_node = ET.SubElement(inputs_node, "input")
            _add_child(input_node, "filename", str(spec.filename))
            _add_child(input_node, "options", " ".join(spec.options))

        outputs_node = ET.SubElement(node, "outputs")
        for spec in mission.outputs:
            output_node = ET.SubElement(outputs_node, "output")
            _add_child(output_node, "filename", str(spec.filename))
            _add_child(output_node, "options", " ".join(spec.options))

        return node

    @staticmethod
    def _decode_mission(node: ET.Element) -> Mission:
        """从 XML 元素反序列化为 Mission 对象。"""

        def get_text(name: str) -> str | None:
            return _text(node.find(name))

        mission_id_str = get_text("mission_id")
        mission_id = ulid.from_str(mission_id_str) if mission_id_str else ulid.new()

        ffmpeg = get_text("ffmpeg") or "ffmpeg"
        source = Path(get_text("source") or "")
        standard_target = Path(get_text("standard_target") or "")

        overwrite_text = get_text("overwrite")
        overwrite = overwrite_text == "true" if overwrite_text else False

        hardware_accelerate = get_text("hardware_accelerate") or None

        options = _parse_options(get_text("options"))

        preset_id = get_text("preset_id") or None
        preset_name = get_text("preset_name") or None

        inputs: list[InputSpec] = []
        inputs_node = node.find("inputs")
        if inputs_node:
            for input_node in inputs_node.findall("input"):
                filename = Path(_text(input_node.find("filename")) or "")
                opts = _parse_options(_text(input_node.find("options")))
                inputs.append(InputSpec(filename=filename, options=opts))

        outputs: list[OutputSpec] = []
        outputs_node = node.find("outputs")
        if outputs_node:
            for output_node in outputs_node.findall("output"):
                filename = Path(_text(output_node.find("filename")) or "")
                opts = _parse_options(_text(output_node.find("options")))
                outputs.append(OutputSpec(filename=filename, options=opts))

        return Mission(
            mission_id=mission_id,
            ffmpeg=ffmpeg,
            source=source,
            standard_target=standard_target,
            overwrite=overwrite,
            hardware_accelerate=hardware_accelerate,
            options=options,
            inputs=inputs,
            outputs=outputs,
            preset_id=preset_id,
            preset_name=preset_name,
        )


def _add_child(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """添加带文本内容的子元素。"""
    child = ET.SubElement(parent, tag)
    child.text = text
    return child
