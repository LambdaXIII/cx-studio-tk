from collections.abc import Iterable, Generator
import xml.etree.ElementTree as ET


import ulid
from .mission import Mission
from pathlib import Path
from .argument_group import ArgumentGroup
from cx_studio.utils import PathUtils


class MissionXML:
    def __init__(self) -> None:
        self.root = ET.Element("missions")

    @staticmethod
    def _encode_argument_group(
        group: ArgumentGroup, name: str | None = None
    ) -> ET.Element:
        node = ET.Element(name or "argument_group")
        if group.filename:
            node.set("filename", str(group.filename))

        arguments = list(group.iter_arguments())
        if arguments:
            node.text = " ".join(arguments)

        return node

    @staticmethod
    def encode_mission_node(mission: Mission):
        mission_node = ET.Element("mission")
        mission_node.set("mission_id", str(mission.mission_id))
        mission_node.set("preset_id", mission.preset_id)
        mission_node.set("preset_name", mission.preset_name)

        mission_node.set("source", str(mission.source))
        mission_node.set("standard_target", str(mission.standard_target))

        ffmpeg_node = ET.SubElement(mission_node, "ffmpeg")
        ffmpeg_node.text = mission.ffmpeg

        # source_node = ET.SubElement(mission_node, "source")
        # source_node.text = str(mission.source)

        # std_target_node = ET.SubElement(mission_node, "standard_target")
        # std_target_node.text = str(mission.standard_target)

        overwrite_node = ET.SubElement(mission_node, "overwrite")
        overwrite_node.text = "YES" if mission.overwrite else "NO"

        hwaccel_node = ET.SubElement(mission_node, "hardware_accelerate")
        hwaccel_node.text = mission.hardware_accelerate

        options_node = MissionXML._encode_argument_group(mission.options, "options")
        mission_node.append(options_node)

        inputs_node = ET.SubElement(mission_node, "inputs")
        for input_group in mission.inputs:
            inputs_node.append(MissionXML._encode_argument_group(input_group))

        output_node = ET.SubElement(mission_node, "outputs")
        for output_group in mission.outputs:
            output_node.append(MissionXML._encode_argument_group(output_group))

        return mission_node

    def add_mission(self, mission: Mission):
        mission_node = MissionXML.encode_mission_node(mission)
        self.root.append(mission_node)

    def add_missions(self, missions: Iterable[Mission]):
        for mission in missions:
            self.add_mission(mission)

    def __len__(self):
        return len(self.root.findall("mission"))

    @staticmethod
    def _decode_argument_group(node: ET.Element) -> ArgumentGroup:
        filename = node.get("filename")
        args = node.text.split(" ") if node.text else []
        return ArgumentGroup(
            options=args, filename=Path(filename) if filename else None
        )

    @staticmethod
    def decode_mission_node(node: ET.Element) -> Mission:
        mission_id = ulid.from_str(str(node.get("mission_id")))
        preset_id = str(node.get("preset_id"))
        preset_name = str(node.get("preset_name"))
        source = str(node.get("source"))
        standard_target = str(node.get("standard_target"))

        def get_subnode_text(name: str) -> str | None:
            subnode = node.find(name)
            return subnode.text if subnode else None

        ffmpeg = get_subnode_text("ffmpeg")

        overwrite = get_subnode_text("overwrite") == "YES"
        hardware_accelerate = get_subnode_text("hardware_accelerate")

        options_node = node.find("options")
        options = (
            MissionXML._decode_argument_group(options_node) if options_node else None
        )

        inputs = []
        inputs_node = node.find("inputs")
        if inputs_node:
            for input_node in inputs_node.findall("argument_group"):
                inputs.append(MissionXML._decode_argument_group(input_node))

        outputs = []
        outputs_node = node.find("outputs")
        if outputs_node:
            for output_node in outputs_node.findall("argument_group"):
                outputs.append(MissionXML._decode_argument_group(output_node))

        return Mission(
            preset_id=preset_id,
            preset_name=preset_name,
            ffmpeg=ffmpeg or "ffmpeg",
            source=Path(source or ""),
            standard_target=Path(standard_target or ""),
            overwrite=overwrite,
            hardware_accelerate=hardware_accelerate or "auto",
            options=options or ArgumentGroup(),
            inputs=inputs,
            outputs=outputs,
            mission_id=mission_id,
        )

    def iter_missions(self) -> Generator[Mission, None, None]:
        for mission_node in self.root.findall("mission"):
            yield MissionXML.decode_mission_node(mission_node)

    def clear(self):
        self.root.clear()

    def save(self, path: Path):
        tree = ET.ElementTree(self.root)
        path = PathUtils.ensure_parents(path)
        tree.write(path, encoding="utf-8", xml_declaration=True)

    @classmethod
    def load(cls, path: Path):
        tree = ET.parse(path)
        root = tree.getroot()
        result = cls()
        result.root = root
        return result
